import 'reflect-metadata';
import { ConsoleLogger } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module.js';

const logger = new ConsoleLogger('RadarAPI', { json: true });
class ConfigurationError extends Error {}

async function bootstrap(): Promise<void> {
  const host = process.env.API_HOST ?? '127.0.0.1';
  const portText = process.env.API_PORT ?? '3001';
  if (host !== '127.0.0.1') {
    throw new ConfigurationError('API_HOST deve ser 127.0.0.1 nesta bancada local.');
  }
  if (!/^\d+$/.test(portText) || Number(portText) < 1 || Number(portText) > 65535) {
    throw new ConfigurationError('API_PORT deve ser um inteiro entre 1 e 65535.');
  }
  const app = await NestFactory.create(AppModule, { logger, abortOnError: false });
  app.setGlobalPrefix('v1');
  app.enableShutdownHooks();
  await app.listen(Number(portText), host);
  logger.log('API local iniciada; liveness disponível em /v1/health/live.');
}

bootstrap().catch((error: unknown) => {
  // Não imprimir ambiente/credenciais ou mensagens de terceiros sem controle.
  logger.error(
    error instanceof ConfigurationError
      ? error.message
      : 'Falha ao iniciar a API. Verifique API_HOST, API_PORT e disponibilidade da porta.',
  );
  process.exitCode = 1;
});
