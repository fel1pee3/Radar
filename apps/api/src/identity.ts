import {
  Controller,
  Get,
  Post,
  Body,
  Req,
  Res,
  UseGuards,
  Inject,
  Injectable,
  UnauthorizedException,
  ForbiddenException,
  HttpCode,
  HttpException,
} from '@nestjs/common';
import type { CanActivate, ExecutionContext } from '@nestjs/common';
import { ApiBody, ApiCookieAuth, ApiOkResponse, ApiOperation, ApiTags } from '@nestjs/swagger';
import type { Request, Response } from 'express';
import { Database } from './database.js';
import { SETTINGS } from './config.js';
import type { Settings } from './config.js';
import type { Role } from './generated/prisma/enums.js';
import { LoginDto } from './dto.js';
import {
  checkPassword,
  hashPassword,
  newToken,
  SESSION_COOKIE,
  SESSION_TTL_MS,
  sessionToken,
  tokenHash,
} from './security.js';

export interface Principal {
  id: string;
  tenantId: string;
  email: string;
  role: Role;
}
export type HumanRequest = Request & { principal: Principal; sessionId: string };

export function assertOrigin(request: Request, settings: Settings): void {
  if (request.headers.origin !== settings.webOrigin) {
    throw new ForbiddenException('Origem ausente ou não autorizada.');
  }
}

@Injectable()
export class OriginGuard implements CanActivate {
  constructor(@Inject(SETTINGS) private readonly settings: Settings) {}
  canActivate(context: ExecutionContext): boolean {
    assertOrigin(context.switchToHttp().getRequest<Request>(), this.settings);
    return true;
  }
}

@Injectable()
export class HumanGuard implements CanActivate {
  constructor(
    private readonly database: Database,
    @Inject(SETTINGS) private readonly settings: Settings,
  ) {}
  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<HumanRequest>();
    const token = sessionToken(request);
    if (!token || request.headers.authorization)
      throw new UnauthorizedException('Sessão inválida ou expirada.');
    const session = await this.database.session.findUnique({
      where: { tokenHash: tokenHash(token), revokedAt: null, expiresAt: { gt: new Date() } },
      include: { user: true },
    });
    if (!session?.user.active) throw new UnauthorizedException('Sessão inválida ou expirada.');
    request.principal = {
      id: session.user.id,
      tenantId: session.tenantId,
      email: session.user.email,
      role: session.user.role,
    };
    request.sessionId = session.id;
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method)) assertOrigin(request, this.settings);
    return true;
  }
}

@Injectable()
export class OwnerGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    if (context.switchToHttp().getRequest<HumanRequest>().principal?.role !== 'OWNER') {
      throw new ForbiddenException('A operação exige um proprietário.');
    }
    return true;
  }
}

@Injectable()
export class LoginLimiter {
  private readonly attempts = new Map<string, { count: number; until: number }>();
  consume(ip: string, email: string): void {
    const now = Date.now();
    for (const [key, entry] of this.attempts) if (entry.until <= now) this.attempts.delete(key);
    for (const [key, limit] of [
      [`ip:${tokenHash(ip)}`, 60],
      [`email:${tokenHash(email)}`, 10],
    ] as const) {
      const previous = this.attempts.get(key);
      if ((!previous && this.attempts.size >= 5000) || (previous && previous.count >= limit)) {
        throw new HttpException('Muitas tentativas. Aguarde cinco minutos.', 429);
      }
      this.attempts.set(key, {
        count: (previous?.count ?? 0) + 1,
        until: previous?.until ?? now + 300000,
      });
    }
  }
}

@ApiTags('auth')
@Controller('auth')
export class IdentityController {
  private readonly dummyHash = hashPassword(newToken('ses'));
  constructor(
    private readonly database: Database,
    private readonly limiter: LoginLimiter,
    @Inject(SETTINGS) private readonly settings: Settings,
  ) {}

  @Post('login')
  @HttpCode(200)
  @UseGuards(OriginGuard)
  @ApiOperation({ summary: 'Inicia sessão opaca de oito horas; exige Origin da web.' })
  @ApiBody({ type: LoginDto })
  @ApiOkResponse({ description: 'Usuário público e cookie HttpOnly; nunca retorna token no JSON.' })
  async login(
    @Body() body: LoginDto,
    @Req() request: Request,
    @Res({ passthrough: true }) response: Response,
  ) {
    const email = body.email.toLowerCase();
    this.limiter.consume(request.ip ?? 'local', email);
    const user = await this.database.user.findUnique({ where: { email } });
    const valid = await checkPassword(user?.passwordHash ?? (await this.dummyHash), body.password);
    if (!user || !user.active || !valid) {
      if (user)
        await this.database.auditEntry.create({
          data: { tenantId: user.tenantId, actorId: user.id, action: 'LOGIN_FAILED' },
        });
      throw new UnauthorizedException('E-mail ou senha inválidos.');
    }
    const token = newToken('ses');
    const expiresAt = new Date(Date.now() + SESSION_TTL_MS);
    const previousToken = sessionToken(request);
    await this.database.$transaction(async (tx) => {
      if (previousToken)
        await tx.session.updateMany({
          where: { tokenHash: tokenHash(previousToken), revokedAt: null },
          data: { revokedAt: new Date() },
        });
      await tx.session.create({
        data: { tenantId: user.tenantId, userId: user.id, tokenHash: tokenHash(token), expiresAt },
      });
      await tx.auditEntry.create({
        data: { tenantId: user.tenantId, actorId: user.id, action: 'LOGIN_SUCCEEDED' },
      });
    });
    response.cookie(SESSION_COOKIE, token, {
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
      secure: this.settings.secureCookie,
      maxAge: SESSION_TTL_MS,
    });
    response.setHeader('Cache-Control', 'no-store');
    return { id: user.id, tenantId: user.tenantId, email: user.email, role: user.role, expiresAt };
  }

  @Get('me')
  @UseGuards(HumanGuard)
  @ApiCookieAuth('human-session')
  @ApiOkResponse({ description: 'Usuário autenticado, sem hash ou token.' })
  me(@Req() request: HumanRequest) {
    return request.principal;
  }

  @Post('logout')
  @HttpCode(204)
  @UseGuards(HumanGuard)
  @ApiCookieAuth('human-session')
  async logout(
    @Req() request: HumanRequest,
    @Res({ passthrough: true }) response: Response,
  ): Promise<void> {
    await this.database.$transaction([
      this.database.session.update({
        where: { id: request.sessionId },
        data: { revokedAt: new Date() },
      }),
      this.database.auditEntry.create({
        data: {
          tenantId: request.principal.tenantId,
          actorId: request.principal.id,
          action: 'LOGOUT',
        },
      }),
    ]);
    response.clearCookie(SESSION_COOKIE, {
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
      secure: this.settings.secureCookie,
    });
  }
}
