import {
  Controller,
  Post,
  Delete,
  Get,
  Param,
  ParseUUIDPipe,
  Req,
  UseGuards,
  Injectable,
  UnauthorizedException,
  NotFoundException,
  HttpCode,
  Res,
} from '@nestjs/common';
import type { CanActivate, ExecutionContext } from '@nestjs/common';
import { ApiBearerAuth, ApiCookieAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import type { Request, Response } from 'express';
import { Database } from './database.js';
import { HumanGuard, OwnerGuard } from './identity.js';
import type { HumanRequest } from './identity.js';
import { newToken, tokenHash, validToken } from './security.js';

type DeviceRequest = Request & {
  worker: { tenantId: string; cameraId: string; deviceId: string; credentialId: string };
};

@Injectable()
export class WorkerGuard implements CanActivate {
  constructor(private readonly database: Database) {}
  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<DeviceRequest>();
    const token = request.headers.authorization?.match(/^Bearer (dev_[A-Za-z0-9_-]{43})$/)?.[1];
    if (!validToken(token, 'dev'))
      throw new UnauthorizedException('Credencial de worker inválida ou revogada.');
    const credential = await this.database.deviceCredential.findUnique({
      where: { tokenHash: tokenHash(token), revokedAt: null },
      include: { device: true },
    });
    if (!credential) throw new UnauthorizedException('Credencial de worker inválida ou revogada.');
    request.worker = {
      tenantId: credential.tenantId,
      cameraId: credential.device.cameraId,
      deviceId: credential.deviceId,
      credentialId: credential.id,
    };
    return true;
  }
}

@ApiTags('device-credentials')
@ApiCookieAuth('human-session')
@UseGuards(HumanGuard, OwnerGuard)
@Controller()
export class DeviceCredentialsController {
  constructor(private readonly database: Database) {}
  @Post('cameras/:id/device-credentials')
  @ApiOperation({
    summary: 'Emite token uma vez e revoga todos os anteriores, preservando Device.',
  })
  async issue(
    @Req() request: HumanRequest,
    @Param('id', ParseUUIDPipe) cameraId: string,
    @Res({ passthrough: true }) response: Response,
  ) {
    const { tenantId, id: actorId } = request.principal;
    const token = newToken('dev');
    const credential = await this.database.$transaction(async (tx) => {
      // UPDATE serializa emissões concorrentes na identidade estável do Device.
      const found = await tx.device.findFirst({ where: { tenantId, cameraId } });
      if (!found) throw new NotFoundException('Câmera não encontrada.');
      const device = await tx.device.update({
        where: { tenantId_id: { tenantId, id: found.id } },
        data: { credentialVersion: { increment: 1 } },
      });
      await tx.deviceCredential.updateMany({
        where: { tenantId, deviceId: device.id, revokedAt: null },
        data: { revokedAt: new Date() },
      });
      const created = await tx.deviceCredential.create({
        data: {
          tenantId,
          deviceId: device.id,
          tokenHash: tokenHash(token),
          version: device.credentialVersion,
        },
        select: { id: true, deviceId: true, version: true, createdAt: true },
      });
      await tx.auditEntry.create({
        data: { tenantId, actorId, action: 'DEVICE_CREDENTIAL_ISSUED', objectId: created.id },
      });
      return created;
    });
    response.setHeader('Cache-Control', 'no-store');
    return { ...credential, cameraId, token };
  }
  @Delete('device-credentials/:id')
  @HttpCode(204)
  async revoke(
    @Req() request: HumanRequest,
    @Param('id', ParseUUIDPipe) id: string,
  ): Promise<void> {
    const { tenantId, id: actorId } = request.principal;
    await this.database.$transaction(async (tx) => {
      const changed = await tx.deviceCredential.updateMany({
        where: { tenantId, id, revokedAt: null },
        data: { revokedAt: new Date() },
      });
      if (!changed.count && !(await tx.deviceCredential.findFirst({ where: { tenantId, id } })))
        throw new NotFoundException('Credencial não encontrada.');
      if (changed.count)
        await tx.auditEntry.create({
          data: { tenantId, actorId, action: 'DEVICE_CREDENTIAL_REVOKED', objectId: id },
        });
    });
  }
}

@ApiTags('edge')
@ApiBearerAuth('worker-token')
@UseGuards(WorkerGuard)
@Controller('edge')
export class EdgeIdentityController {
  @Get('me')
  @ApiOperation({ summary: 'Diagnóstico de autenticação e escopo do worker; não ingere eventos.' })
  me(@Req() request: DeviceRequest) {
    return request.worker;
  }
}
