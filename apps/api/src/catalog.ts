import {
  Body,
  Controller,
  Get,
  Post,
  Patch,
  Param,
  ParseUUIDPipe,
  Query,
  Req,
  UseGuards,
  NotFoundException,
  BadRequestException,
  Inject,
} from '@nestjs/common';
import { ApiCookieAuth, ApiTags } from '@nestjs/swagger';
import { Database } from './database.js';
import { HumanGuard, OwnerGuard } from './identity.js';
import type { HumanRequest } from './identity.js';
import { CameraDto, CameraPatchDto, ListDto, SiteDto, SitePatchDto } from './dto.js';
import { pageArguments, pageResult } from './pagination.js';
import { CLOCK } from './event-support.js';
import type { Clock } from './event-support.js';
import { cameraHealth } from './heartbeat.js';

export const siteSelect = {
  id: true,
  tenantId: true,
  name: true,
  timezone: true,
  createdAt: true,
  updatedAt: true,
} as const;
export const cameraSelect = {
  id: true,
  tenantId: true,
  siteId: true,
  name: true,
  type: true,
  expectedRunning: true,
  evidenceMode: true,
  snapshotAuthorizedAt: true,
  lastHeartbeat: true,
  heartbeatReceivedAt: true,
  createdAt: true,
  updatedAt: true,
  device: { select: { id: true } },
} as const;

@ApiTags('sites')
@ApiCookieAuth('human-session')
@UseGuards(HumanGuard)
@Controller('sites')
export class SitesController {
  constructor(private readonly database: Database) {}
  @Get()
  async list(@Req() request: HumanRequest, @Query() query: ListDto) {
    const args = pageArguments(query);
    const rows = await this.database.site.findMany({
      ...args,
      where: { ...args.where, tenantId: request.principal.tenantId },
      orderBy: [{ createdAt: 'asc' }, { id: 'asc' }],
      select: siteSelect,
    });
    return pageResult(rows, query.limit);
  }
  @Get(':id')
  async get(@Req() request: HumanRequest, @Param('id', ParseUUIDPipe) id: string) {
    const site = await this.database.site.findUnique({
      where: { tenantId_id: { tenantId: request.principal.tenantId, id } },
      select: siteSelect,
    });
    if (!site) throw new NotFoundException('Local não encontrado.');
    return site;
  }
  @Post()
  @UseGuards(OwnerGuard)
  async create(@Req() request: HumanRequest, @Body() body: SiteDto) {
    const { tenantId, id: actorId } = request.principal;
    return this.database.$transaction(async (tx) => {
      const site = await tx.site.create({ data: { ...body, tenantId }, select: siteSelect });
      await tx.auditEntry.create({
        data: { tenantId, actorId, action: 'SITE_CREATED', objectId: site.id },
      });
      return site;
    });
  }
  @Patch(':id')
  @UseGuards(OwnerGuard)
  async update(
    @Req() request: HumanRequest,
    @Param('id', ParseUUIDPipe) id: string,
    @Body() body: SitePatchDto,
  ) {
    if (Object.keys(body).length === 0)
      throw new BadRequestException('Informe ao menos uma alteração.');
    const { tenantId, id: actorId } = request.principal;
    return this.database.$transaction(async (tx) => {
      const site = await tx.site.update({
        where: { tenantId_id: { tenantId, id } },
        data: body,
        select: siteSelect,
      });
      await tx.auditEntry.create({
        data: { tenantId, actorId, action: 'SITE_UPDATED', objectId: id },
      });
      return site;
    });
  }
}

@ApiTags('cameras')
@ApiCookieAuth('human-session')
@UseGuards(HumanGuard)
@Controller('cameras')
export class CamerasController {
  constructor(
    private readonly database: Database,
    @Inject(CLOCK) private readonly clock: Clock,
  ) {}
  private present<
    T extends {
      lastHeartbeat: unknown;
      heartbeatReceivedAt: Date | null;
      expectedRunning: boolean;
    },
  >(camera: T) {
    const { lastHeartbeat, heartbeatReceivedAt, ...result } = camera;
    void lastHeartbeat;
    void heartbeatReceivedAt;
    return { ...result, health: cameraHealth(camera, this.clock.now()) };
  }
  @Get()
  async list(@Req() request: HumanRequest, @Query() query: ListDto) {
    const args = pageArguments(query);
    const rows = await this.database.camera.findMany({
      ...args,
      where: { ...args.where, tenantId: request.principal.tenantId },
      orderBy: [{ createdAt: 'asc' }, { id: 'asc' }],
      select: cameraSelect,
    });
    const page = pageResult(rows, query.limit);
    return { ...page, items: page.items.map((camera) => this.present(camera)) };
  }
  @Get(':id')
  async get(@Req() request: HumanRequest, @Param('id', ParseUUIDPipe) id: string) {
    const camera = await this.database.camera.findUnique({
      where: { tenantId_id: { tenantId: request.principal.tenantId, id } },
      select: cameraSelect,
    });
    if (!camera) throw new NotFoundException('Câmera não encontrada.');
    return this.present(camera);
  }
  @Post()
  @UseGuards(OwnerGuard)
  async create(@Req() request: HumanRequest, @Body() body: CameraDto) {
    const { tenantId, id: actorId } = request.principal;
    return this.database.$transaction(async (tx) => {
      if (!(await tx.site.findUnique({ where: { tenantId_id: { tenantId, id: body.siteId } } })))
        throw new NotFoundException('Local não encontrado.');
      const camera = await tx.camera.create({ data: { ...body, tenantId } });
      await tx.device.create({ data: { tenantId, cameraId: camera.id } });
      await tx.auditEntry.create({
        data: { tenantId, actorId, action: 'CAMERA_CREATED', objectId: camera.id },
      });
      return this.present(
        await tx.camera.findUniqueOrThrow({ where: { id: camera.id }, select: cameraSelect }),
      );
    });
  }
  @Patch(':id')
  @UseGuards(OwnerGuard)
  async update(
    @Req() request: HumanRequest,
    @Param('id', ParseUUIDPipe) id: string,
    @Body() body: CameraPatchDto,
  ) {
    if (Object.keys(body).length === 0)
      throw new BadRequestException('Informe ao menos uma alteração.');
    const { tenantId, id: actorId } = request.principal;
    return this.database.$transaction(async (tx) => {
      if (
        body.siteId &&
        !(await tx.site.findUnique({ where: { tenantId_id: { tenantId, id: body.siteId } } }))
      )
        throw new NotFoundException('Local não encontrado.');
      const camera = await tx.camera.update({
        where: { tenantId_id: { tenantId, id } },
        data: body,
        select: cameraSelect,
      });
      await tx.auditEntry.create({
        data: { tenantId, actorId, action: 'CAMERA_UPDATED', objectId: id },
      });
      return this.present(camera);
    });
  }
}
