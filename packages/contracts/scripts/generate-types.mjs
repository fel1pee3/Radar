import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { compile } from 'json-schema-to-typescript';
import { format } from 'prettier';

const root = new URL('../', import.meta.url);
mkdirSync(new URL('src/generated/', root), { recursive: true });
for (const name of ['event-v1', 'heartbeat-v1', 'incident-action-v1']) {
  const schema = JSON.parse(readFileSync(new URL(`src/schemas/${name}.json`, root), 'utf8'));
  const generated = await compile(schema, schema.title, {
    bannerComment: '/* Gerado do JSON Schema versionado. Execute pnpm contracts:generate. */',
    unknownAny: true,
    maxItems: 0,
  });
  const output = await format(generated, {
    parser: 'typescript',
    singleQuote: true,
    trailingComma: 'all',
    printWidth: 100,
  });
  const target = new URL(`src/generated/${name}.ts`, root);
  if (process.argv.includes('--check')) {
    if (readFileSync(target, 'utf8') !== output)
      throw new Error(`Tipos desatualizados para ${name}.`);
  } else writeFileSync(target, output);
}
