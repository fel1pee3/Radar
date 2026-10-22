import {
  Controller,
  Injectable,
  Inject,
  Get,
  Post,
  Delete,
  Patch,
  Param,
  Req,
  Res,
  Body,
  UseGuards,
  ParseUUIDPipe,
  Logger,
} from '@nestjs/common';
import type { OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import {
  ApiBearerAuth,
  ApiCookieAuth,
  ApiTags,
  ApiBody,
  ApiProperty,
  ApiProduces,
  ApiConsumes,
} from '@nestjs/swagger';
import type { Response } from 'express';
import { IsIn, IsBoolean } from 'class-validator';
import { createHash, randomUUID } from 'node:crypto';
import { resolve, relative, isAbsolute, dirname, join } from 'node:path';
import { mkdir, readdir, lstat, readFile, open, unlink } from 'node:fs/promises';
import sharp from 'sharp';
import { Database } from './database.js';
import { SETTINGS } from './config.js';
import type { Settings } from './config.js';
import { CLOCK, fail, lockCamera } from './event-support.js';
import type { Clock, Transaction } from './event-support.js';
import { HumanGuard, OwnerGuard } from './identity.js';
import type { Principal, HumanRequest } from './identity.js';
import { WorkerGuard } from './devices.js';
import type { DeviceRequest } from './devices.js';
import { Prisma } from './generated/prisma/client.js';

const DAY = 86400000;
const MAX_BYTES = 2 * 1024 * 1024;
const MAX_PIXELS = 1280 * 1280;
const sha = (b: Buffer) => createHash('sha256').update(b).digest('hex');
const filePattern = /^[0-9a-f-]{36}\.jpg$/;

export class EvidencePreferenceDto {
  @ApiProperty({ enum: ['none', 'skeleton', 'snapshot'] })
  @IsIn(['none', 'skeleton', 'snapshot'])
  mode!: 'none' | 'skeleton' | 'snapshot';
  @IsBoolean() authorized!: boolean;
}
export class RetentionPreferenceDto {
  @IsBoolean() enabled!: boolean;
}

@Injectable()
export class EvidenceService {
  readonly directory: string;
  private decoders = 0;
  constructor(
    private readonly db: Database,
    @Inject(SETTINGS) private readonly settings: Settings,
    @Inject(CLOCK) private readonly clock: Clock,
  ) {
    // Absolute paths are allowed only under this repository's private root.
    const repo = process.cwd().endsWith(join('apps', 'api')) ? resolve('../..') : process.cwd();
    const privateRoot = resolve(repo, '.local');
    this.directory = resolve(repo, settings.localDataDir ?? '.local/api-evidence');
    const rel = relative(privateRoot, this.directory);
    if (!rel || rel.startsWith('..') || isAbsolute(rel)) fail(500, 'PRIVATE_STORAGE_REQUIRED');
  }
  async locked<T>(fn: (tx: Transaction) => Promise<T>): Promise<T> {
    return this.db.$transaction(
      async (tx) => {
        // One local storage namespace: serialize file mutation, reads and reconciliation.
        await tx.$executeRaw`SELECT pg_advisory_xact_lock(707, 707)`;
        return fn(tx);
      },
      { maxWait: 10000, timeout: 15000 },
    );
  }
  async root() {
    await mkdir(this.directory, { recursive: true, mode: 0o700 });
    let path = this.directory;
    while (true) {
      if ((await lstat(path)).isSymbolicLink()) fail(503, 'EVIDENCE_STORAGE_UNAVAILABLE');
      const parent = dirname(path);
      if (parent === path) break;
      path = parent;
    }
  }
  path(key: string) {
    if (!filePattern.test(key)) fail(503, 'EVIDENCE_STORAGE_UNAVAILABLE');
    return join(this.directory, key);
  }
  async write(key: string, data: Buffer) {
    await this.root();
    const names = await readdir(this.directory);
    if (names.length >= 1000) fail(507, 'EVIDENCE_STORAGE_FULL');
    let bytes = 0;
    for (const name of names) {
      const stat = await lstat(join(this.directory, name));
      if (stat.isFile()) bytes += stat.size;
    }
    if (bytes + data.length > 128 * 1024 * 1024) fail(507, 'EVIDENCE_STORAGE_FULL');
    const file = await open(this.path(key), 'wx', 0o600);
    try {
      await file.writeFile(data);
      await file.sync();
    } finally {
      await file.close();
    }
  }
  async removeFile(key: string) {
    await this.root();
    const path = this.path(key);
    try {
      const stat = await lstat(path);
      if (!stat.isFile() || stat.isSymbolicLink()) fail(503, 'EVIDENCE_STORAGE_UNAVAILABLE');
      await unlink(path);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
    }
  }
  async bytes(key: string) {
    await this.root();
    const path = this.path(key);
    const stat = await lstat(path);
    if (!stat.isFile() || stat.isSymbolicLink() || stat.size > MAX_BYTES)
      fail(503, 'EVIDENCE_STORAGE_UNAVAILABLE');
    return readFile(path);
  }
  async incident(tx: Transaction, principal: Principal, id: string) {
    const row = await tx.incident.findUnique({
      where: { tenantId_id: { tenantId: principal.tenantId, id } },
      include: { evidence: true },
    });
    if (!row) fail(404, 'INCIDENT_NOT_FOUND');
    return row;
  }
  async describe(principal: Principal, id: string) {
    return this.locked(async (tx) => {
      const incident = await this.incident(tx, principal, id);
      const e = incident.evidence;
      return {
        mode: incident.evidenceMode,
        state: e
          ? e.expiresAt <= this.clock.now() && !['DELETED', 'EXPIRED'].includes(e.state)
            ? 'EXPIRED'
            : e.state
          : 'DISABLED',
        expiresAt: e?.expiresAt ?? null,
      };
    });
  }
  async upload(worker: DeviceRequest['worker'], eventId: string, input: unknown) {
    if (!Buffer.isBuffer(input) || input.length < 4) fail(422, 'INVALID_JPEG');
    if (input.length > MAX_BYTES) fail(413, 'SNAPSHOT_TOO_LARGE');
    if (input[0] !== 255 || input[1] !== 216 || input[2] !== 255) fail(422, 'INVALID_JPEG');
    if (this.decoders >= 2) fail(429, 'IMAGE_DECODER_BUSY');
    this.decoders++;
    try {
      let output: Buffer;
      try {
        const image = sharp(input, {
          limitInputPixels: MAX_PIXELS,
          failOn: 'warning',
          sequentialRead: true,
        });
        const meta = await image.metadata();
        if (
          meta.format !== 'jpeg' ||
          !meta.width ||
          !meta.height ||
          Math.max(meta.width, meta.height) > 1280 ||
          meta.width * meta.height > MAX_PIXELS ||
          (meta.pages ?? 1) > 1
        )
          fail(422, 'INVALID_JPEG_DIMENSIONS');
        output = await image.rotate().jpeg({ quality: 85 }).timeout({ seconds: 3 }).toBuffer();
      } catch {
        fail(422, 'INVALID_JPEG');
      }
      if (output.length > MAX_BYTES) fail(413, 'SNAPSHOT_TOO_LARGE');
      const hash = sha(input);
      return await this.locked(async (tx) => {
        await lockCamera(tx, worker.tenantId, worker.cameraId);
        const receipt = await tx.eventReceipt.findUnique({
          where: { deviceId_eventId: { deviceId: worker.deviceId, eventId } },
        });
        if (!receipt) fail(404, 'EVENT_NOT_FOUND');
        if (!receipt.incidentId || receipt.expiredAt) fail(410, 'EVENT_EXPIRED');
        const incident = await tx.incident.findUniqueOrThrow({
          where: { id: receipt.incidentId },
          include: { evidence: true, camera: true },
        });
        if (incident.cameraId !== worker.cameraId) fail(403, 'CAMERA_SCOPE_MISMATCH');
        if (incident.originEventId !== eventId) fail(409, 'SNAPSHOT_ORIGIN_EVENT_REQUIRED');
        const e = incident.evidence;
        if (!e) fail(403, 'SNAPSHOT_DISABLED');
        if (
          e.deletedAt ||
          e.expiresAt <= this.clock.now() ||
          ['DELETED', 'EXPIRED'].includes(e.state)
        )
          fail(410, 'EVIDENCE_EXPIRED');
        if (
          incident.camera.evidenceMode !== 'snapshot' ||
          !incident.camera.snapshotAuthorizedAt ||
          incident.camera.snapshotAuthorizedAt > incident.receivedAt
        )
          fail(403, 'SNAPSHOT_NOT_AUTHORIZED');
        if (e.inputHash && e.inputHash !== hash) fail(409, 'SNAPSHOT_CONTENT_CONFLICT');
        const duplicate = !!e.inputHash;
        let key = e.objectKey;
        if (key) {
          try {
            if (sha(await this.bytes(key)) !== e.storedHash)
              fail(503, 'EVIDENCE_STORAGE_UNAVAILABLE');
          } catch (error) {
            // Only the identical, already hashed original can repair a missing file.
            // Neither deletion markers nor its original expiry are changed.
            if ((error as NodeJS.ErrnoException).code !== 'ENOENT')
              fail(503, 'EVIDENCE_STORAGE_UNAVAILABLE');
            key = null;
          }
        }
        if (!key) {
          key = `${randomUUID()}.jpg`;
          try {
            await this.write(key, output);
          } catch {
            fail(503, 'EVIDENCE_STORAGE_UNAVAILABLE');
          }
        }
        const receivedAt = e.receivedAt ?? this.clock.now();
        await tx.evidence.update({
          where: { id: e.id },
          data: {
            state: 'AVAILABLE',
            inputHash: hash,
            storedHash: sha(output),
            objectKey: key,
            bytes: output.length,
            receivedAt,
            expiresAt: new Date(receivedAt.getTime() + DAY),
          },
        });
        return { eventId, incidentId: incident.id, hash, duplicate };
      });
    } finally {
      this.decoders--;
    }
  }
  async read(principal: Principal, id: string) {
    return this.locked(async (tx) => {
      const incident = await this.incident(tx, principal, id),
        e = incident.evidence;
      if (!e) fail(404, 'EVIDENCE_DISABLED');
      if (
        e.deletedAt ||
        e.expiresAt <= this.clock.now() ||
        ['DELETED', 'EXPIRED'].includes(e.state)
      )
        fail(410, 'EVIDENCE_EXPIRED');
      if (e.state !== 'AVAILABLE' || !e.objectKey) fail(404, 'EVIDENCE_PENDING');
      let data: Buffer;
      try {
        data = await this.bytes(e.objectKey);
        if (sha(data) !== e.storedHash) throw new Error();
      } catch {
        fail(503, 'EVIDENCE_STORAGE_UNAVAILABLE');
      }
      await tx.auditEntry.create({
        data: {
          tenantId: principal.tenantId,
          actorId: principal.id,
          incidentId: id,
          objectId: e.id,
          action: 'SNAPSHOT_ACCESSED',
          resultCode: 'READ',
          createdAt: this.clock.now(),
        },
      });
      return data;
    });
  }
  async delete(principal: Principal, id: string) {
    await this.locked(async (tx) => {
      const incident = await this.incident(tx, principal, id),
        e = incident.evidence;
      if (!e) fail(404, 'EVIDENCE_DISABLED');
      if (e.state === 'DELETED' || e.state === 'EXPIRED') return;
      await tx.evidence.update({
        where: { id: e.id },
        data: { state: 'DELETED', deletedAt: this.clock.now() },
      });
      await tx.auditEntry.create({
        data: {
          tenantId: principal.tenantId,
          actorId: principal.id,
          incidentId: id,
          objectId: e.id,
          action: 'SNAPSHOT_DELETED',
          resultCode: 'COMMITTED',
          createdAt: this.clock.now(),
        },
      });
    }); // Commit tombstone BEFORE unlink. A crash cannot resurrect the image.
    await this.reconcile();
    return { state: 'DELETED' };
  }
  async reconcile() {
    return this.locked(async (tx) => {
      await this.root();
      const rows = await tx.evidence.findMany();
      for (const e of rows) {
        if ((e.deletedAt || ['DELETED', 'EXPIRED'].includes(e.state)) && e.objectKey) {
          try {
            await this.removeFile(e.objectKey);
          } catch {
            fail(503, 'EVIDENCE_CLEANUP_PENDING');
          }
          await tx.evidence.update({ where: { id: e.id }, data: { objectKey: null, bytes: 0 } });
        }
      }
      const keys = new Set(
        rows
          .filter((e) => !e.deletedAt && !['DELETED', 'EXPIRED'].includes(e.state))
          .map((e) => e.objectKey),
      );
      for (const name of await readdir(this.directory)) {
        if (filePattern.test(name) && !keys.has(name)) await this.removeFile(name);
      }
    });
  }
  async retain() {
    const now = this.clock.now();
    // Marks are durable before file cleanup. Reads enforce expiry even if job fails.
    await this.locked(async (tx) => {
      await tx.evidence.updateMany({
        where: { state: { in: ['AVAILABLE', 'AWAITING'] }, expiresAt: { lte: now } },
        data: { state: 'EXPIRED', deletedAt: now },
      });
    });
    await this.reconcile();
    await this.locked(async (tx) => {
      const cameras = await tx.camera.findMany({ select: { id: true, tenantId: true } });
      for (const camera of cameras) {
        await lockCamera(tx, camera.tenantId, camera.id);
        const old = new Date(now.getTime() - 7 * DAY);
        await tx.incident.updateMany({
          where: { cameraId: camera.id, receivedAt: { lte: old }, poseRedactedAt: null },
          data: { pose: Prisma.DbNull, poseRedactedAt: now },
        });
        const receipts = await tx.eventReceipt.findMany({
          where: { device: { cameraId: camera.id }, receivedAt: { lte: old }, redactedAt: null },
        });
        for (const r of receipts)
          await tx.eventReceipt.update({
            where: { id: r.id },
            data: { payload: Prisma.DbNull, redactedAt: now },
          });
        const purge = await tx.tenant.findUniqueOrThrow({ where: { id: camera.tenantId } });
        if (purge.metadataRetentionEnabled) {
          const incidents = await tx.incident.findMany({
            where: { cameraId: camera.id, receivedAt: { lte: new Date(now.getTime() - 30 * DAY) } },
          });
          for (const i of incidents) {
            const evidence = await tx.evidence.findUnique({ where: { incidentId: i.id } });
            if (evidence?.objectKey) continue; // Never orphan a file by purging metadata.
            await tx.eventReceipt.updateMany({
              where: { incidentId: i.id },
              data: { incidentId: null, expiredAt: now, payload: Prisma.DbNull, redactedAt: now },
            });
            await tx.auditEntry.deleteMany({ where: { incidentId: i.id } });
            await tx.incidentAction.deleteMany({ where: { incidentId: i.id } });
            const intent = await tx.notificationIntent.findUnique({ where: { incidentId: i.id } });
            if (intent)
              await tx.notificationDelivery.deleteMany({ where: { intentId: intent.id } });
            await tx.notificationIntent.deleteMany({ where: { incidentId: i.id } });
            await tx.evidence.deleteMany({ where: { incidentId: i.id } });
            await tx.incident.delete({ where: { id: i.id } });
          }
        }
      }
      const cutoff = new Date(now.getTime() - 90 * DAY);
      await tx.eventReceipt.deleteMany({
        where: { receivedAt: { lte: cutoff }, incidentId: null, expiredAt: { not: null } },
      });
      // Active leases remain. Retired run IDs remain 90 days.
      await tx.cameraRun.deleteMany({ where: { retiredAt: { lte: cutoff } } });
      const tenants = await tx.tenant.findMany({ where: { metadataRetentionEnabled: true } });
      for (const t of tenants)
        await tx.auditEntry.deleteMany({
          where: {
            tenantId: t.id,
            createdAt: { lte: new Date(now.getTime() - 30 * DAY) },
            incidentId: null,
          },
        });
    });
    return { status: 'ok', at: now.toISOString() };
  }
}

@ApiTags('evidence')
@ApiBearerAuth('worker-token')
@UseGuards(WorkerGuard)
@Controller('edge/events')
export class SnapshotController {
  constructor(private readonly evidence: EvidenceService) {}
  @Post(':eventId/snapshot')
  @ApiConsumes('image/jpeg')
  @ApiBody({ schema: { type: 'string', format: 'binary' } })
  upload(@Req() req: DeviceRequest, @Param('eventId', ParseUUIDPipe) id: string) {
    return this.evidence.upload(req.worker, id, req.body);
  }
}
@ApiTags('evidence')
@ApiCookieAuth('human-session')
@UseGuards(HumanGuard)
@Controller('incidents')
export class EvidenceController {
  constructor(private readonly evidence: EvidenceService) {}
  @Get(':id/snapshot')
  @ApiProduces('image/jpeg')
  async read(
    @Req() req: HumanRequest,
    @Param('id', ParseUUIDPipe) id: string,
    @Res() res: Response,
  ) {
    const data = await this.evidence.read(req.principal, id);
    res.setHeader('Content-Type', 'image/jpeg');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('Content-Disposition', 'inline');
    res.send(data);
  }
  @Delete(':id/snapshot')
  @UseGuards(OwnerGuard)
  delete(@Req() req: HumanRequest, @Param('id', ParseUUIDPipe) id: string) {
    return this.evidence.delete(req.principal, id);
  }
}
@ApiTags('evidence')
@ApiCookieAuth('human-session')
@UseGuards(HumanGuard, OwnerGuard)
@Controller()
export class PreferencesController {
  constructor(
    private readonly db: Database,
    @Inject(CLOCK) private readonly clock: Clock,
  ) {}
  @Patch('cameras/:id/evidence-preference')
  async evidence(
    @Req() req: HumanRequest,
    @Param('id', ParseUUIDPipe) id: string,
    @Body() body: EvidencePreferenceDto,
  ) {
    if (body.mode === 'snapshot' && !body.authorized) fail(422, 'SNAPSHOT_AUTHORIZATION_REQUIRED');
    return this.db.$transaction(async (tx) => {
      await lockCamera(tx, req.principal.tenantId, id);
      const row = await tx.camera.update({
        where: { tenantId_id: { tenantId: req.principal.tenantId, id } },
        data: {
          evidenceMode: body.mode,
          snapshotAuthorizedAt: body.mode === 'snapshot' ? this.clock.now() : null,
        },
      });
      await tx.auditEntry.create({
        data: {
          tenantId: req.principal.tenantId,
          actorId: req.principal.id,
          objectId: id,
          action: 'EVIDENCE_PREFERENCE_CHANGED',
          resultCode: body.mode.toUpperCase(),
          createdAt: this.clock.now(),
        },
      });
      return { mode: row.evidenceMode, authorizedAt: row.snapshotAuthorizedAt };
    });
  }
  @Get('retention-preference')
  async get(@Req() req: HumanRequest) {
    const row = await this.db.tenant.findUniqueOrThrow({ where: { id: req.principal.tenantId } });
    return { enabled: row.metadataRetentionEnabled };
  }
  @Patch('retention-preference')
  async retention(@Req() req: HumanRequest, @Body() body: RetentionPreferenceDto) {
    return this.db.$transaction(async (tx) => {
      await tx.tenant.update({
        where: { id: req.principal.tenantId },
        data: { metadataRetentionEnabled: body.enabled },
      });
      await tx.auditEntry.create({
        data: {
          tenantId: req.principal.tenantId,
          actorId: req.principal.id,
          action: 'RETENTION_PREFERENCE_CHANGED',
          resultCode: body.enabled ? 'ENABLED' : 'DISABLED',
          createdAt: this.clock.now(),
        },
      });
      return body;
    });
  }
}
@Injectable()
export class RetentionJob implements OnModuleInit, OnModuleDestroy {
  private timer?: ReturnType<typeof setInterval>;
  private busy = false;
  private readonly logger = new Logger('Retention');
  constructor(
    private readonly evidence: EvidenceService,
    @Inject(SETTINGS) private readonly settings: Settings,
  ) {}
  onModuleInit() {
    if (!this.settings.retentionEnabled) return;
    void this.run();
    this.timer = setInterval(() => void this.run(), 60000);
    this.timer.unref();
  }
  onModuleDestroy() {
    if (this.timer) clearInterval(this.timer);
  }
  async run() {
    if (this.busy) return;
    this.busy = true;
    try {
      return await this.evidence.retain();
    } catch {
      this.logger.error({ event: 'retention_failed', code: 'CLEANUP_PENDING' });
    } finally {
      this.busy = false;
    }
  }
}
