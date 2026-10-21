import { Controller, Get, ServiceUnavailableException } from '@nestjs/common';
import { ApiTags, ApiResponse } from '@nestjs/swagger';
import type { HealthLiveResponse } from '@radar/contracts';
import { Database } from './database.js';

@ApiTags('health')
@Controller('health')
export class HealthController {
  constructor(private readonly database: Database) {}
  @Get('live')
  live(): HealthLiveResponse {
    return { status: 'ok' };
  }

  @Get('ready')
  @ApiResponse({ status: 503, description: 'Banco indisponível.' })
  async ready(): Promise<HealthLiveResponse> {
    try {
      await this.database.$queryRaw`SELECT 1`;
      return { status: 'ok' };
    } catch {
      throw new ServiceUnavailableException('Banco temporariamente indisponível.');
    }
  }
}
