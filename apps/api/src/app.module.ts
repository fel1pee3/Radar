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

@Module({
  controllers: [
    HealthController,
    IdentityController,
    SitesController,
    CamerasController,
    DeviceCredentialsController,
    EdgeIdentityController,
  ],
  providers: [Database, HumanGuard, OwnerGuard, OriginGuard, LoginLimiter, WorkerGuard],
})
export class AppModule {
  static register(settings: Settings): DynamicModule {
    return { module: AppModule, providers: [{ provide: SETTINGS, useValue: settings }] };
  }
}
