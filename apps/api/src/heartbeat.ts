import {
  Body,
  Controller,
  Post,
  Req,
  UseGuards,
  Injectable,
  Inject,
  HttpCode,
} from '@nestjs/common';
import { ApiBearerAuth, ApiBody, ApiTags } from '@nestjs/swagger';
import type { HeartbeatV1 } from '@radar/contracts';
import { Database } from './database.js';
import { WorkerGuard } from './devices.js';
import type { DeviceRequest } from './devices.js';
import { CLOCK, ContractPipe, fail, lockCamera } from './event-support.js';
import type { Clock } from './event-support.js';

export function cameraHealth(
  camera: { lastHeartbeat: unknown; heartbeatReceivedAt: Date | null; expectedRunning: boolean },
  now: Date,
) {
  const heartbeat = camera.lastHeartbeat as HeartbeatV1 | null;
  const age = camera.heartbeatReceivedAt
    ? Math.max(0, now.getTime() - camera.heartbeatReceivedAt.getTime())
    : null;
  const stale = age === null || age > 15000;
  let state: 'ONLINE' | 'DEGRADED' | 'OFFLINE' | 'PAUSED' | 'SOURCE_ENDED' = 'OFFLINE';
  if (heartbeat?.captureState === 'PAUSED') state = 'PAUSED';
  else if (heartbeat?.captureState === 'ENDED') state = 'SOURCE_ENDED';
  else if (heartbeat && !stale)
    state =
      heartbeat.captureState === 'ERROR' || heartbeat.qualityFlags.length ? 'DEGRADED' : 'ONLINE';
  return {
    state,
    expectedRunning: camera.expectedRunning,
    receivedAt: camera.heartbeatReceivedAt,
    ageMs: age,
    stale,
    heartbeat,
  };
}

@Injectable()
export class HeartbeatService {
  constructor(
    private readonly database: Database,
    @Inject(CLOCK) private readonly clock: Clock,
  ) {}
  async accept(worker: DeviceRequest['worker'], heartbeat: HeartbeatV1) {
    if (heartbeat.cameraId.toLowerCase() !== worker.cameraId) fail(403, 'CAMERA_SCOPE_MISMATCH');
    return this.database.$transaction(
      async (tx) => {
        await lockCamera(tx, worker.tenantId, worker.cameraId);
        const camera = await tx.camera.findUniqueOrThrow({ where: { id: worker.cameraId } });
        const now = this.clock.now();
        const run = await tx.cameraRun.findUnique({
          where: {
            tenantId_cameraId_runId: {
              tenantId: worker.tenantId,
              cameraId: worker.cameraId,
              runId: heartbeat.runId,
            },
          },
        });
        const previous = camera.lastHeartbeat as unknown as HeartbeatV1 | null;
        if (run?.retiredAt)
          return {
            accepted: false,
            ignored: true,
            reason: 'RETIRED_RUN',
            health: cameraHealth(camera, now),
          };
        if (camera.activeRunId === heartbeat.runId.toLowerCase()) {
          if (
            camera.heartbeatSequence !== null &&
            BigInt(heartbeat.sequence) <= camera.heartbeatSequence
          )
            return {
              accepted: false,
              ignored: true,
              reason: 'OLD_SEQUENCE',
              health: cameraHealth(camera, now),
            };
          if (previous?.captureState === 'ENDED') fail(409, 'RUN_CLOSED');
        } else if (camera.activeRunId) {
          const leaseValid =
            camera.heartbeatReceivedAt &&
            now.getTime() - camera.heartbeatReceivedAt.getTime() <= 15000;
          if (leaseValid && previous?.captureState !== 'ENDED') fail(409, 'RUN_CONFLICT');
          await tx.cameraRun.update({
            where: {
              tenantId_cameraId_runId: {
                tenantId: worker.tenantId,
                cameraId: worker.cameraId,
                runId: camera.activeRunId,
              },
            },
            data: { retiredAt: now },
          });
        }
        if (!run)
          await tx.cameraRun.create({
            data: {
              tenantId: worker.tenantId,
              cameraId: worker.cameraId,
              runId: heartbeat.runId,
              firstReceivedAt: now,
            },
          });
        const updated = await tx.camera.update({
          where: { id: worker.cameraId },
          data: {
            activeRunId: heartbeat.runId,
            heartbeatSequence: BigInt(heartbeat.sequence),
            heartbeatReceivedAt: now,
            lastHeartbeat: { ...heartbeat },
          },
        });
        return { accepted: true, ignored: false, health: cameraHealth(updated, now) };
      },
      { maxWait: 10000, timeout: 10000 },
    );
  }
}

@ApiTags('edge')
@ApiBearerAuth('worker-token')
@UseGuards(WorkerGuard)
@Controller('edge')
export class HeartbeatController {
  constructor(private readonly heartbeat: HeartbeatService) {}
  @Post('heartbeat')
  @HttpCode(200)
  @ApiBody({ schema: { $ref: '#/components/schemas/HeartbeatV1' } })
  accept(@Req() request: DeviceRequest, @Body(new ContractPipe('heartbeat-v1')) body: HeartbeatV1) {
    return this.heartbeat.accept(request.worker, body);
  }
}
