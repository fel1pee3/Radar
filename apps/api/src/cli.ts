import 'reflect-metadata';
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createDatabase } from './database.js';
import { ConfigurationError, validateDatabaseUrl } from './config.js';
import { seed, createOperator } from './bootstrap.js';
import { createApplication } from './application.js';

async function main(): Promise<void> {
  const command = process.argv[2];
  if (command === 'openapi') {
    const { app, document } = await createApplication(undefined, false);
    try {
      writeFileSync(
        fileURLToPath(new URL('../../../docs/OPENAPI.json', import.meta.url)),
        `${JSON.stringify(document, null, 2)}\n`,
      );
    } finally {
      await app.close();
    }
    console.log('OpenAPI gerado em docs/OPENAPI.json.');
    return;
  }
  if (!['seed', 'operator'].includes(command ?? ''))
    throw new ConfigurationError('Comando local inválido.');
  const database = createDatabase(validateDatabaseUrl(process.env.DATABASE_URL));
  try {
    const result =
      command === 'seed'
        ? await seed(database, {
            email: process.env.BOOTSTRAP_EMAIL ?? '',
            password: process.env.BOOTSTRAP_PASSWORD ?? '',
            tenantSlug: process.env.BOOTSTRAP_TENANT_SLUG,
            tenantName: process.env.BOOTSTRAP_TENANT_NAME,
            siteName: process.env.BOOTSTRAP_SITE_NAME,
            timezone: process.env.BOOTSTRAP_SITE_TIMEZONE,
          })
        : await createOperator(database, {
            email: process.env.OPERATOR_EMAIL ?? '',
            password: process.env.OPERATOR_PASSWORD ?? '',
            tenantSlug: process.env.BOOTSTRAP_TENANT_SLUG,
          });
    console.log(JSON.stringify({ status: 'ok', command, ...result }));
  } finally {
    await database.$disconnect();
  }
}
main().catch((error: unknown) => {
  console.error(
    JSON.stringify({
      status: 'error',
      message:
        error instanceof ConfigurationError
          ? error.message
          : 'Não foi possível provisionar. Confira e-mail/senha privados, tenant, migrações e disponibilidade do banco. Nenhuma senha existente é sobrescrita.',
    }),
  );
  process.exitCode = 1;
});
