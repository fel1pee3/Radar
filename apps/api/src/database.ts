import { Injectable, Inject } from '@nestjs/common';
import type { OnModuleDestroy } from '@nestjs/common';
import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from './generated/prisma/client.js';
import { SETTINGS } from './config.js';
import type { Settings } from './config.js';

export function createDatabase(databaseUrl: string): PrismaClient {
  const adapter = new PrismaPg({
    connectionString: databaseUrl,
    max: 5,
    connectionTimeoutMillis: 2000,
    idleTimeoutMillis: 5000,
    statement_timeout: 3000,
  });
  return new PrismaClient({ adapter, log: [], errorFormat: 'minimal' });
}

@Injectable()
export class Database extends PrismaClient implements OnModuleDestroy {
  constructor(@Inject(SETTINGS) settings: Settings) {
    super({
      adapter: new PrismaPg({
        connectionString: settings.databaseUrl,
        max: 5,
        connectionTimeoutMillis: 2000,
        idleTimeoutMillis: 5000,
        statement_timeout: 3000,
      }),
      log: [],
      errorFormat: 'minimal',
    });
  }
  async onModuleDestroy(): Promise<void> {
    await this.$disconnect();
  }
}
