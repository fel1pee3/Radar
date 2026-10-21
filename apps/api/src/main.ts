import 'reflect-metadata';
import { ConsoleLogger } from '@nestjs/common';
import { createApplication } from './application.js';
import { ConfigurationError, readSettings } from './config.js';

const logger = new ConsoleLogger('RadarAPI', { json: true });

async function bootstrap(): Promise<void> {
  const settings = readSettings();
  const { app } = await createApplication(settings, logger);
  app.enableShutdownHooks();
  await app.listen(settings.port, settings.host);
  logger.log('API local iniciada; /v1/health/live e /v1/health/ready disponíveis.');
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
