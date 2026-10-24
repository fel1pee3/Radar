import { spawn } from 'node:child_process';
import { mkdirSync, openSync, closeSync, writeFileSync } from 'node:fs';
import { sourceIdentity } from './source.mjs';
const directory = '.local/etapa08';
mkdirSync(directory, { recursive: true });
const source = sourceIdentity(),
  checks = [];
const save = () =>
  writeFileSync(
    `${directory}/engineering.json`,
    JSON.stringify(
      {
        schemaVersion: 1,
        source,
        createdAt: new Date().toISOString(),
        checks,
        releaseReady: false,
        scope: 'Automated engineering only. Physical, perception and offline gates separate.',
      },
      null,
      2,
    ),
  );
const jobs = [
  ['frozen-js', 'pnpm', ['install', '--frozen-lockfile']],
  ['frozen-python', 'uv', ['sync', '--project', 'services/edge', '--frozen']],
  ['lint', 'pnpm', ['lint']],
  ['typecheck', 'pnpm', ['typecheck']],
  ['build', 'pnpm', ['build']],
  ['edge-lint', 'pnpm', ['lint:edge']],
  ['edge-env', 'pnpm', ['check:edge']],
  ['contracts', 'pnpm', ['test:contracts']],
  ['simulator', 'pnpm', ['test:demo']],
  [
    'python',
    'uv',
    ['run', '--project', 'services/edge', '--frozen', 'pytest', 'services/edge/tests', '-q'],
  ],
  ['api', 'pnpm', ['test:api']],
  ['browser', 'pnpm', ['test:e2e']],
  ['backup', 'pnpm', ['test:backup']],
  ['clean-install', 'pnpm', ['demo:install-check']],
];
for (const [name, tool, args] of jobs) {
  const start = Date.now(),
    log = `${directory}/verify-${name}.log`,
    fd = openSync(log, 'w');
  const command = tool === 'pnpm' ? process.execPath : 'uv';
  const argv = tool === 'pnpm' ? [process.env.npm_execpath, ...args] : args;
  console.log(`Executando ${name}; log privado: ${log}`);
  const child = spawn(command, argv, {
    env: { ...process.env, RADAR_TEST_GUI: '1', PYTHONIOENCODING: 'utf-8' },
    stdio: ['ignore', fd, fd],
    windowsHide: true,
  });
  const exitCode = await new Promise((r) => {
    child.once('error', () => r(1));
    child.once('exit', (code) => r(code ?? 1));
  });
  closeSync(fd);
  checks.push({
    name,
    command: `${tool} ${args.join(' ')}`,
    exitCode,
    log,
    seconds: (Date.now() - start) / 1000,
  });
  save();
  console.log(`${name}: ${exitCode === 0 ? 'APROVADO' : 'FALHOU'}`);
  if (exitCode) {
    process.exitCode = 1;
    break;
  }
}
if (sourceIdentity().sourceSha256 !== source.sourceSha256) {
  console.error('Código mudou durante a execução; resultados não validam a revisão atual.');
  checks.push({ name: 'stable-source', exitCode: 1 });
  save();
  process.exitCode = 1;
}
