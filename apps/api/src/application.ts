import { ConsoleLogger, ValidationPipe, BadRequestException } from '@nestjs/common';
import type { LoggerService } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import type { NestExpressApplication } from '@nestjs/platform-express';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import type { Application, Request, Response, NextFunction } from 'express';
import { AppModule } from './app.module.js';
import { readSettings } from './config.js';
import type { Settings } from './config.js';
import { SafeExceptionFilter } from './errors.js';
import { schemas } from '@radar/contracts';
import type { Clock } from './event-support.js';

export async function createApplication(
  settings: Settings = readSettings(),
  logger: LoggerService | false = new ConsoleLogger('RadarAPI', { json: true }),
  options: { clock?: Clock; notificationsEnabled?: boolean } = {},
) {
  const app = await NestFactory.create<NestExpressApplication>(
    AppModule.register(settings, options),
    {
      logger,
      abortOnError: false,
      bodyParser: false,
    },
  );
  const server = app.getHttpAdapter().getInstance() as Application;
  server.disable('x-powered-by');
  server.set('trust proxy', false);
  app.use((request: Request, response: Response, next: NextFunction) => {
    response.setHeader('Cache-Control', 'no-store');
    response.setHeader('X-Content-Type-Options', 'nosniff');
    next();
  });
  app.useBodyParser('json', { limit: '64kb', strict: true });
  app.setGlobalPrefix('v1');
  app.useGlobalPipes(
    new ValidationPipe({
      transform: true,
      whitelist: true,
      forbidNonWhitelisted: true,
      forbidUnknownValues: true,
      exceptionFactory: () => new BadRequestException('Dados inválidos ou campos não permitidos.'),
    }),
  );
  app.useGlobalFilters(new SafeExceptionFilter());
  const document = SwaggerModule.createDocument(
    app,
    new DocumentBuilder()
      .setTitle('Radar de Acontecimentos — API local')
      .setVersion('0.1.0')
      .addCookieAuth('radar_session', { type: 'apiKey', in: 'cookie' }, 'human-session')
      .addBearerAuth({ type: 'http', scheme: 'bearer', bearerFormat: 'opaque' }, 'worker-token')
      .build(),
  );
  document.openapi = '3.1.0';
  for (const schema of Object.values(schemas)) {
    // Nest tipa schemas em OAS 3.0; o documento servido declara 3.1 para os JSON Schemas v1.
    document.components!.schemas![schema.title] = schema as unknown as NonNullable<
      NonNullable<typeof document.components>['schemas']
    >[string];
  }
  SwaggerModule.setup('v1/docs', app, document, { ui: false, jsonDocumentUrl: '/v1/openapi.json' });
  return { app, document };
}
