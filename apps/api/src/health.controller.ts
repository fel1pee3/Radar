import { Controller, Get } from '@nestjs/common';
import type { HealthLiveResponse } from '@radar/contracts';

@Controller('health')
export class HealthController {
  @Get('live')
  live(): HealthLiveResponse {
    return { status: 'ok' };
  }
}
