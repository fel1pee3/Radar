import { randomBytes } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

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
