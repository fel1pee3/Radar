import { randomBytes } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { parseEnv } from 'node:util';

const root = new URL('../', import.meta.url);
for (const name of ['.env', 'apps/api/.env', 'apps/web/.env']) {
  const target = new URL(name, root);
  if (existsSync(target)) {
    console.log(`Preservado: ${name}`);
    continue;
  }
  const example = readFileSync(new URL(`${name}.example`, root), 'utf8');
  const content =
    name === '.env'
      ? example.replace(
          /^POSTGRES_PASSWORD=$/m,
          `POSTGRES_PASSWORD=${randomBytes(32).toString('hex')}`,
        )
      : example;
  writeFileSync(fileURLToPath(target), content, { flag: 'wx', mode: 0o600 });
  console.log(`Criado: ${name} (valores privados omitidos)`);
}

// Atualização aditiva da etapa 01. Não altera valores privados já preenchidos.
const database = parseEnv(readFileSync(new URL('.env', root), 'utf8'));
if (!database.POSTGRES_USER || !database.POSTGRES_PASSWORD || !database.POSTGRES_DB) {
  throw new Error('Defina as credenciais privadas do PostgreSQL no .env raiz.');
}
const port = database.POSTGRES_PORT ?? '5432';
if (port === '5432') {
  throw new Error(
    'Configure POSTGRES_PORT=15432 no .env: a porta 5432 pertence ao PostgreSQL existente.',
  );
}
const apiFile = new URL('apps/api/.env', root);
let apiText = readFileSync(apiFile, 'utf8');
const apiValues = parseEnv(apiText);
const defaults = {
  DATABASE_URL: `postgresql://${encodeURIComponent(database.POSTGRES_USER)}:${encodeURIComponent(database.POSTGRES_PASSWORD)}@127.0.0.1:${port}/${database.POSTGRES_DB}`,
  WEB_ORIGIN: 'http://127.0.0.1:3000',
  NODE_ENV: 'development',
  ALLOW_INSECURE_LOCAL_HTTP: 'true',
};
let changed = false;
for (const [key, value] of Object.entries(defaults)) {
  if (apiValues[key]) continue;
  const entry = `${key}=${JSON.stringify(value)}`;
  if (Object.hasOwn(apiValues, key)) {
    apiText = apiText.replace(new RegExp(`^${key}=.*$`, 'm'), entry);
  } else {
    apiText += `\n${entry}\n`;
  }
  changed = true;
}
if (changed) {
  writeFileSync(apiFile, apiText, { mode: 0o600 });
  console.log('Configuração da API complementada; valores privados omitidos.');
}
