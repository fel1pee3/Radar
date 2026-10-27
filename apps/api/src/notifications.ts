import { Controller, Get, Injectable, Inject, Logger, Query, Req, UseGuards } from '@nestjs/common';
import type { OnApplicationBootstrap, OnModuleDestroy } from '@nestjs/common';
import { ApiCookieAuth, ApiTags } from '@nestjs/swagger';
import { Database } from './database.js';
import { deliveryClass, CLOCK, NOTIFICATIONS_ENABLED } from './event-support.js';
import type { Clock } from './event-support.js';
import { HumanGuard } from './identity.js';
import type { HumanRequest } from './identity.js';
import { ListDto } from './dto.js';
import { pageArguments, pageResult } from './pagination.js';

@Injectable()
export class NotificationExecutor implements OnApplicationBootstrap, OnModuleDestroy {
  private readonly logger = new Logger('LocalNotifications');
  private timer?: ReturnType<typeof setInterval>;
  private current?: Promise<void>;
  private stopping = false;
  constructor(
    private readonly database: Database,
    @Inject(CLOCK) private readonly clock: Clock,
    @Inject(NOTIFICATIONS_ENABLED) private readonly enabled: boolean,
  ) {}
  onApplicationBootstrap(): void {
    if (!this.enabled) return;
    this.tick();
    this.timer = setInterval(() => this.tick(), 1000);
    this.timer.unref();
  }
  private tick(): void {
    if (this.current || this.stopping) return;
    this.current = this.drain()
      .then(() => undefined)
      .catch(() => {
        this.logger.warn({
          event: 'simulated_notification_retry',
          code: 'DATABASE_OR_TRANSACTION_UNAVAILABLE',
        });
      })
      .finally(() => {
        this.current = undefined;
      });
  }
  async onModuleDestroy(): Promise<void> {
    this.stopping = true;
    if (this.timer) clearInterval(this.timer);
    await this.current;
  }
  async drain(limit = 20): Promise<number> {
    let total = 0;
    while (total < limit) {
      const processed = await this.database.$transaction(
        async (tx) => {
          const now = this.clock.now();
          const candidates = await tx.$queryRaw<
            { id: string }[]
          >`SELECT "id" FROM "NotificationIntent" WHERE "status"='PENDING' AND "nextAttemptAt" <= ${now} ORDER BY "nextAttemptAt", "createdAt", "id" FOR UPDATE SKIP LOCKED LIMIT 1`;
          if (!candidates.length) return false;
          const intent = await tx.notificationIntent.findUniqueOrThrow({
            where: { id: candidates[0]!.id },
            include: { incident: true, delivery: true },
          });
          const dispatchedAt = this.clock.now();
          const hint =
            intent.incident.deliveryClass === 'DELAYED' ||
            intent.incident.deliveryClass === 'CLOCK_UNCERTAIN'
              ? intent.incident.deliveryClass
              : undefined;
          const currentClass = deliveryClass(
            {
              mode: intent.incident.mode,
              detectedAt: intent.incident.detectedAt.toISOString(),
              occurredAt: intent.incident.occurredAt.toISOString(),
            },
            dispatchedAt,
            hint,
          );
          if (!intent.delivery) {
            await tx.notificationDelivery.create({
              data: {
                tenantId: intent.tenantId,
                intentId: intent.id,
                channel: 'SIMULATED',
                urgent: currentClass === 'CURRENT',
                createdAt: dispatchedAt,
                message: `Aviso local SIMULATED: ${intent.incident.kind}; modo ${intent.incident.mode}; ${currentClass}. Nenhuma mensagem externa enviada.`,
              },
            });
            await tx.auditEntry.create({
              data: {
                tenantId: intent.tenantId,
                incidentId: intent.incidentId,
                objectId: intent.id,
                action: 'SIMULATED_NOTIFICATION_RECORDED',
                resultCode:
                  currentClass === intent.incident.deliveryClass
                    ? 'RECORDED_LOCALLY'
                    : 'RECORDED_LOCALLY_' + currentClass,
                createdAt: dispatchedAt,
              },
            });
          }
          await tx.notificationIntent.update({
            where: { id: intent.id },
            data: { status: 'DELIVERED', attempts: { increment: 1 }, lastErrorCode: null },
          });
          return true;
        },
        { maxWait: 10000, timeout: 10000 },
      );
      if (!processed) break;
      total++;
    }
    return total;
  }
}

@ApiTags('notifications')
@ApiCookieAuth('human-session')
@UseGuards(HumanGuard)
@Controller('notifications')
export class NotificationsController {
  constructor(private readonly database: Database) {}
  @Get()
  async list(@Req() request: HumanRequest, @Query() query: ListDto) {
    const args = pageArguments(query);
    const rows = await this.database.notificationDelivery.findMany({
      ...args,
      where: { ...args.where, tenantId: request.principal.tenantId },
      orderBy: [{ createdAt: 'asc' }, { id: 'asc' }],
      include: {
        intent: {
          select: {
            incidentId: true,
            incident: {
              select: {
                mode: true,
                deliveryClass: true,
                kind: true,
                occurredAt: true,
                cameraId: true,
              },
            },
          },
        },
      },
    });
    return pageResult(rows, query.limit);
  }
}
