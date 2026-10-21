import { Body, Controller, Post, Req, Res, UseGuards, Injectable, Inject } from '@nestjs/common';
import { ApiBearerAuth, ApiBody, ApiResponse, ApiTags } from '@nestjs/swagger';
import type { Response } from 'express';
import type { EventV1 } from '@radar/contracts';
import { Database } from './database.js';
import { WorkerGuard } from './devices.js';
import type { DeviceRequest } from './devices.js';
import {
  CLOCK,
  ContractPipe,
  contentHash,
  deliveryClass,
  episodeHash,
  fail,
  lockCamera,
} from './event-support.js';
import type { Clock } from './event-support.js';

@Injectable()
export class IngestService {
  constructor(
    private readonly database: Database,
    @Inject(CLOCK) private readonly clock: Clock,
  ) {}
  async accept(worker: DeviceRequest['worker'], event: EventV1) {
    if (event.cameraId.toLowerCase() !== worker.cameraId) fail(403, 'CAMERA_SCOPE_MISMATCH');
    const hash = contentHash(event);
    return this.database.$transaction(
      async (tx) => {
        await lockCamera(tx, worker.tenantId, worker.cameraId);
        const previous = await tx.eventReceipt.findUnique({
          where: { deviceId_eventId: { deviceId: worker.deviceId, eventId: event.eventId } },
        });
        if (previous) {
          if (previous.expiredAt || !previous.incidentId) fail(410, 'EVENT_EXPIRED');
          if (previous.payloadHash !== hash) fail(409, 'EVENT_ID_CONFLICT');
          return {
            status: 200,
            body: {
              eventId: event.eventId,
              incidentId: previous.incidentId,
              receivedAt: previous.receivedAt,
              duplicate: true,
              deliveryClass: previous.deliveryClass,
            },
          };
        }
        const receivedAt = this.clock.now();
        const age = receivedAt.getTime() - Date.parse(event.detectedAt);
        if (age > 30 * 86400000) fail(410, 'EVENT_TOO_OLD');
        if (age < -86400000) fail(422, 'INVALID_EVENT_TIME');
        let incident = await tx.incident.findUnique({
          where: { cameraId_episodeId: { cameraId: worker.cameraId, episodeId: event.episodeId } },
        });
        const duplicate = !!incident;
        const immutableHash = episodeHash(event);
        if (incident && incident.episodeHash !== immutableHash) fail(409, 'EPISODE_CONFLICT');
        if (!incident) {
          const camera = await tx.camera.findUniqueOrThrow({ where: { id: worker.cameraId } });
          incident = await tx.incident.create({
            data: {
              tenantId: worker.tenantId,
              cameraId: worker.cameraId,
              siteId: camera.siteId,
              episodeId: event.episodeId,
              originEventId: event.eventId,
              runId: event.runId,
              episodeHash: immutableHash,
              kind: event.kind,
              mode: event.mode,
              deliveryClass: deliveryClass(event, receivedAt),
              occurredAt: new Date(event.occurredAt),
              detectedAt: new Date(event.detectedAt),
              receivedAt,
              sourceOffsetMs: event.sourceOffsetMs === null ? null : BigInt(event.sourceOffsetMs),
              signals: event.signals,
              pose: event.pose,
              versions: event.versions,
              createdAt: receivedAt,
              updatedAt: receivedAt,
            },
          });
          await tx.auditEntry.create({
            data: {
              tenantId: worker.tenantId,
              incidentId: incident.id,
              objectId: incident.id,
              action: 'INCIDENT_CREATED',
              resultCode: 'COMMITTED',
              toVersion: 1,
              createdAt: receivedAt,
            },
          });
          await tx.notificationIntent.create({
            data: {
              tenantId: worker.tenantId,
              incidentId: incident.id,
              key: `incident:${incident.id}:initial`,
              nextAttemptAt: receivedAt,
              createdAt: receivedAt,
            },
          });
        }
        await tx.eventReceipt.create({
          data: {
            tenantId: worker.tenantId,
            deviceId: worker.deviceId,
            eventId: event.eventId,
            episodeId: event.episodeId,
            payloadHash: hash,
            payload: event,
            receivedAt,
            deliveryClass: incident.deliveryClass,
            incidentId: incident.id,
          },
        });
        return {
          status: duplicate ? 200 : 201,
          body: {
            eventId: event.eventId,
            incidentId: incident.id,
            receivedAt,
            duplicate,
            deliveryClass: incident.deliveryClass,
          },
        };
      },
      { maxWait: 10000, timeout: 10000 },
    );
  }
}

@ApiTags('edge')
@ApiBearerAuth('worker-token')
@UseGuards(WorkerGuard)
@Controller('edge')
export class IngestController {
  constructor(private readonly ingest: IngestService) {}
  @Post('events')
  @ApiBody({ schema: { $ref: '#/components/schemas/EventV1' } })
  @ApiResponse({
    status: 201,
    description: 'Novo incidente e recibo persistidos na mesma transação.',
  })
  @ApiResponse({ status: 200, description: 'Reenvio ou episódio equivalente, sem novo aviso.' })
  @ApiResponse({ status: 409, description: 'EVENT_ID_CONFLICT ou EPISODE_CONFLICT.' })
  async accept(
    @Req() request: DeviceRequest,
    @Body(new ContractPipe('event-v1')) event: EventV1,
    @Res({ passthrough: true }) response: Response,
  ) {
    const result = await this.ingest.accept(request.worker, event);
    response.status(result.status);
    return result.body;
  }
}
