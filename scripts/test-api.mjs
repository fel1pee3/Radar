import { spawnSync } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { createServer } from 'node:net';

const suffix = randomBytes(6).toString('hex');
const name = `radar-test-${suffix}`;
const database = `radar_test_${suffix}`;
const password = randomBytes(32).toString('hex');
const environment = {
  ...process.env,
  POSTGRES_USER: 'radar_test',
  POSTGRES_DB: database,
  POSTGRES_PASSWORD: password,
  NODE_ENV: 'development',
  ALLOW_INSECURE_LOCAL_HTTP: 'true',
  WEB_ORIGIN: 'http://127.0.0.1:3000',
  RADAR_TEST_CONTAINER: name,
};

function docker(args, options = {}) {
  const result = spawnSync('docker', args, { env: environment, encoding: 'utf8', ...options });
  if (result.status !== 0)
    throw new Error('Falha no Docker de testes. Verifique o daemon e os recursos disponíveis.');
  return result.stdout.trim();
}
function pnpm(args) {
  if (!process.env.npm_execpath) throw new Error('Execute por pnpm.cmd test:api.');
  const result = spawnSync(process.execPath, [process.env.npm_execpath, ...args], {
    env: environment,
    stdio: 'inherit',
  });
  if (result.status !== 0)
    throw new Error('Verificação de integração falhou; consulte os resultados acima.');
}

let created = false;
try {
  const probe = createServer();
  await new Promise((resolve, reject) => {
    probe.once('error', reject);
    probe.listen(0, '127.0.0.1', resolve);
  });
  const address = probe.address();
  if (!address || typeof address === 'string')
    throw new Error('Não foi possível reservar porta local de testes.');
  const fixedPort = address.port;
  await new Promise((resolve, reject) =>
    probe.close((error) => (error ? reject(error) : resolve())),
  );
  // Container exclusivo e descartável; nunca utiliza Compose/volume da demonstração.
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
    `127.0.0.1:${fixedPort}:5432`,
    '--health-cmd',
    `pg_isready -U radar_test -d ${database}`,
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
  for (let attempt = 0; attempt < 40; attempt++) {
    if (docker(['inspect', '--format', '{{.State.Health.Status}}', name]) === 'healthy') {
      healthy = true;
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  if (!healthy) throw new Error('PostgreSQL de testes não ficou saudável.');
  const binding = docker(['port', name, '5432/tcp']);
  const port = binding.match(/^127\.0\.0\.1:(\d+)$/)?.[1];
  if (!port || ['5432', '15432'].includes(port)) throw new Error('Porta de testes não isolada.');
  environment.DATABASE_URL = `postgresql://radar_test:${password}@127.0.0.1:${port}/${database}`;
  console.log(`Banco vazio de testes em container exclusivo ${name}; conexão privada omitida.`);
  pnpm(['--filter', '@radar/api', 'db:migrate']);
  pnpm(['--filter', '@radar/api', 'test:integration']);
} catch (error) {
  console.error(error instanceof Error ? error.message : 'Falha na validação isolada.');
  process.exitCode = 1;
} finally {
  if (created) {
    try {
      docker(['rm', '-f', '-v', name]);
      console.log(
        'Container exclusivo de testes removido. Banco e volume da demonstração preservados.',
      );
    } catch {
      console.error(`Remova somente o container de teste ${name} após verificar o Docker.`);
      process.exitCode = 1;
    }
  }
}
