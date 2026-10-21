import { Module } from '@nestjs/common';
import type { DynamicModule } from '@nestjs/common';
import { HealthController } from './health.controller.js';
import { SETTINGS } from './config.js';
import type { Settings } from './config.js';
import { Database } from './database.js';
import {
  IdentityController,
  HumanGuard,
  OwnerGuard,
  OriginGuard,
  LoginLimiter,
} from './identity.js';
import { SitesController, CamerasController } from './catalog.js';
import { DeviceCredentialsController, EdgeIdentityController, WorkerGuard } from './devices.js';
import { IngestController, IngestService } from './ingest.js';
import { HeartbeatController, HeartbeatService } from './heartbeat.js';
import { IncidentsController, IncidentService, AuditController } from './incidents.js';
import { NotificationsController, NotificationExecutor } from './notifications.js';
import { CLOCK, SystemClock, NOTIFICATIONS_ENABLED } from './event-support.js';
import type { Clock } from './event-support.js';

@Module({
  controllers: [
    HealthController,
    IdentityController,
    SitesController,
    CamerasController,
    DeviceCredentialsController,
    EdgeIdentityController,
    IngestController,
    HeartbeatController,
    IncidentsController,
    AuditController,
    NotificationsController,
  ],
  providers: [
    Database,
    HumanGuard,
    OwnerGuard,
    OriginGuard,
    LoginLimiter,
    WorkerGuard,
    IngestService,
    HeartbeatService,
    IncidentService,
    NotificationExecutor,
  ],
})
export class AppModule {
  static register(
    settings: Settings,
    options: { clock?: Clock; notificationsEnabled?: boolean } = {},
  ): DynamicModule {
    return {
      module: AppModule,
      providers: [
        { provide: SETTINGS, useValue: settings },
        { provide: CLOCK, useValue: options.clock ?? new SystemClock() },
        { provide: NOTIFICATIONS_ENABLED, useValue: options.notificationsEnabled ?? true },
      ],
    };
  }
}
