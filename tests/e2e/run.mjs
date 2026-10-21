import { spawn, spawnSync } from 'node:child_process';
import { createServer } from 'node:net';
import { randomBytes } from 'node:crypto';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { setTimeout as pause } from 'node:timers/promises';
const suffix = randomBytes(6).toString('hex'),
  name = `radar-e2e-${suffix}`,
  database = `radar_e2e_${suffix}`;
const env = {
  ...process.env,
  POSTGRES_USER: 'radar_e2e',
  POSTGRES_DB: database,
  POSTGRES_PASSWORD: randomBytes(32).toString('hex'),
  NODE_ENV: 'development',
  ALLOW_INSECURE_LOCAL_HTTP: 'true',
  RADAR_E2E_CONTAINER: name,
  RADAR_E2E_PASSWORD: `Synthetic-${randomBytes(18).toString('hex')}`,
  RADAR_E2E_BUILD: 'true',
};
function docker(args) {
  const result = spawnSync('docker', args, { env, encoding: 'utf8' });
  if (result.status !== 0) throw new Error('Docker de testes indisponível.');
  return result.stdout.trim();
}
async function freePort() {
  const server = createServer();
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const port = server.address().port;
  await new Promise((resolve) => server.close(resolve));
  if ([3000, 3001, 5432, 15432].includes(port)) return freePort();
  return port;
}
function pnpm(args, overrides = {}) {
  if (!process.env.npm_execpath) throw new Error('Execute via pnpm.cmd test:e2e.');
  const result = spawnSync(process.execPath, [process.env.npm_execpath, ...args], {
    env: { ...env, ...overrides },
    stdio: 'inherit',
  });
  if (result.status !== 0) throw new Error('Comando de testes falhou. Consulte o resultado acima.');
}
function start(args, extra = {}) {
  const child = spawn(process.execPath, args, {
    env: { ...env, ...extra },
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
  });
  let logs = '';
  child.stdout.on('data', (chunk) => {
    logs = (logs + chunk).slice(-10000);
  });
  child.stderr.on('data', (chunk) => {
    logs = (logs + chunk).slice(-10000);
  });
  child.on('error', () => {});
  return { child, logs: () => logs };
}
async function ready(url, process) {
  for (let index = 0; index < 80; index++) {
    if (process.child.exitCode !== null)
      throw new Error('Processo exclusivo encerrou antes de ficar pronto.');
    try {
      if ((await fetch(url, { signal: AbortSignal.timeout(1000) })).ok) return;
    } catch {
      /* aguarda somente o processo próprio */
    }
    await pause(500);
  }
  throw new Error('Processo de testes não ficou pronto.');
}
async function stop(process) {
  if (!process || process.child.exitCode !== null) return;
  process.child.kill();
  await Promise.race([new Promise((resolve) => process.child.once('exit', resolve)), pause(3000)]);
}
let created = false,
  api,
  web;
const originalNextEnv = await readFile('apps/web/next-env.d.ts');
try {
  const [pgPort, apiPort, webPort] = await Promise.all([freePort(), freePort(), freePort()]);
  if (new Set([pgPort, apiPort, webPort]).size !== 3)
    throw new Error('Portas de testes colidiram. Execute novamente.');
  env.DATABASE_URL = `postgresql://radar_e2e:${env.POSTGRES_PASSWORD}@127.0.0.1:${pgPort}/${database}`;
  env.API_HOST = '127.0.0.1';
  env.API_PORT = String(apiPort);
  env.WEB_ORIGIN = `http://127.0.0.1:${webPort}`;
  env.RADAR_E2E_API_URL = `http://127.0.0.1:${apiPort}/v1`;
  env.API_INTERNAL_URL = env.RADAR_E2E_API_URL;
  env.RADAR_E2E_WEB_URL = env.WEB_ORIGIN;
  docker([
    'create',
    '--name',
    name,
    '--memory',
    '512m',
    '--volume',
    '/var/lib/postgresql/data',
    '-e',
    'POSTGRES_USER',
    '-e',
    'POSTGRES_DB',
    '-e',
    'POSTGRES_PASSWORD',
    '--publish',
    `127.0.0.1:${pgPort}:5432`,
    '--health-cmd',
    `pg_isready -U radar_e2e -d ${database}`,
    '--health-interval',
    '1s',
    '--health-timeout',
    '2s',
    '--health-retries',
    '30',
    'postgres:17.11',
  ]);
  created = true;
  docker(['start', name]);
  let healthy = false;
  for (let index = 0; index < 40; index++) {
    if (docker(['inspect', '--format', '{{.State.Health.Status}}', name]) === 'healthy') {
      healthy = true;
      break;
    }
    await pause(1000);
  }
  if (!healthy) throw new Error('Banco exclusivo não ficou pronto.');
  console.log(`E2E: container exclusivo ${name}; portas efêmeras; conexão privada omitida.`);
  pnpm(['--filter', '@radar/api', 'db:migrate']);
  await mkdir('.local/etapa03', { recursive: true });
  await writeFile(
    'apps/web/tsconfig.e2e.json',
    JSON.stringify(
      {
        extends: './tsconfig.json',
        compilerOptions: { incremental: false },
        include: [
          'next-env.d.ts',
          'app/**/*.tsx',
          'components/**/*.tsx',
          'lib/**/*.ts',
          '.next-e2e/types/**/*.ts',
        ],
        exclude: ['node_modules', '.next'],
      },
      null,
      2,
    ),
  );
  pnpm(['--filter', '@radar/web', 'build'], { NODE_ENV: 'production' });
  api = start(['apps/api/dist/main.js']);
  env.RADAR_E2E_API_PID = String(api.child.pid);
  await ready(`${env.RADAR_E2E_API_URL}/health/ready`, api);
  web = start(
    [
      'apps/web/node_modules/next/dist/bin/next',
      'start',
      'apps/web',
      '--hostname',
      '127.0.0.1',
      '--port',
      String(webPort),
    ],
    { NODE_ENV: 'production' },
  );
  await ready(`${env.RADAR_E2E_WEB_URL}/login`, web);
  const test = spawn(
    process.execPath,
    [
      process.env.npm_execpath,
      'exec',
      'playwright',
      'test',
      '--config',
      'tests/e2e/playwright.config.mjs',
      ...process.argv.slice(2),
    ],
    { env, stdio: 'inherit', windowsHide: true },
  );
  const code = await new Promise((resolve, reject) => {
    test.once('error', reject);
    test.once('exit', resolve);
  });
  if (code !== 0) throw new Error('Playwright encontrou falhas. Consulte os resultados acima.');
  for (const process of [api, web]) {
    for (const secret of [env.POSTGRES_PASSWORD, env.DATABASE_URL, env.RADAR_E2E_PASSWORD])
      if (process.logs().includes(secret))
        throw new Error('Segredo apareceu no log do processo exclusivo.');
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : 'Falha E2E.');
  process.exitCode = 1;
} finally {
  await stop(web);
  await stop(api);
  await writeFile('apps/web/next-env.d.ts', originalNextEnv);
  if (created) {
    try {
      docker(['rm', '-f', '-v', name]);
      console.log('Recursos exclusivos E2E removidos; demonstração e porta 5432 preservadas.');
    } catch {
      console.error(`Remova somente o container exclusivo ${name} após conferir o Docker.`);
      process.exitCode = 1;
    }
  }
}
