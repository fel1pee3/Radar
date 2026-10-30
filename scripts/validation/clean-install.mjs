import { spawn, spawnSync, execFileSync } from 'node:child_process';
import { randomBytes, randomUUID } from 'node:crypto';
import { createServer } from 'node:net';
import {
  mkdirSync,
  copyFileSync,
  writeFileSync,
  openSync,
  closeSync,
  existsSync,
  readFileSync,
  realpathSync,
  statSync,
} from 'node:fs';
import { resolve, dirname, basename, isAbsolute, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { docker } from '../backup.mjs';
import { sourceIdentity } from './source.mjs';

function withinLocal(root, value) {
  const path = resolve(root, value);
  const base = resolve(root, '.local');
  const inside = (parent, child) => {
    const rel = relative(parent, child);
    return rel && rel !== '..' && !rel.startsWith('..' + sep) && !isAbsolute(rel);
  };
  if (!inside(base, path)) throw new Error('Use um arquivo privado dentro de .local.');
  let existing = path;
  while (!existsSync(existing)) existing = dirname(existing);
  const canonicalBase = resolve(realpathSync(root), '.local');
  const canonicalExisting = realpathSync(existing);
  if (canonicalExisting !== canonicalBase && !inside(canonicalBase, canonicalExisting))
    throw new Error('Redirecionamento fora de .local não é permitido.');
  return path;
}

export function cleanInstallRuntime(environment = process.env, root = process.cwd()) {
  const requested = environment.RADAR_VALIDATION_RUNTIME || 'PYTHON312';
  if (!['PYTHON312', 'PYTHON313_SIGNED'].includes(requested))
    throw new Error('RADAR_VALIDATION_RUNTIME inválido; use PYTHON312 ou PYTHON313_SIGNED.');
  const project = requested === 'PYTHON313_SIGNED' ? 'experiments/python313-cpu' : 'services/edge';
  let python = null;
  const explicit = [];
  if (requested === 'PYTHON313_SIGNED') {
    if (!environment.RADAR_SIGNED_PYTHON || !isAbsolute(environment.RADAR_SIGNED_PYTHON))
      throw new Error(
        'Informe RADAR_SIGNED_PYTHON com o caminho absoluto do runtime PSF existente.',
      );
    python = withinLocal(root, environment.RADAR_SIGNED_PYTHON);
    if (
      basename(python).toLowerCase() !== 'python.exe' ||
      !existsSync(python) ||
      !statSync(python).isFile()
    )
      throw new Error('RADAR_SIGNED_PYTHON precisa apontar ao python.exe existente.');
    explicit.push('--python', python, '--no-python-downloads');
  }
  return {
    requested,
    project,
    python,
    syncArguments: ['sync', '--project', project, '--frozen', ...explicit],
    runArguments: ['run', '--project', project, '--frozen', ...explicit],
  };
}

export function cleanInstallResultPath(environment = process.env, root = process.cwd()) {
  if (!environment.RADAR_CLEAN_INSTALL_RESULT)
    return resolve(root, '.local/etapa08/clean-install.json');
  const target = withinLocal(root, environment.RADAR_CLEAN_INSTALL_RESULT);
  if (existsSync(target))
    throw new Error('Comprovante existente preservado; use RADAR_CLEAN_INSTALL_RESULT novo.');
  if (!existsSync(dirname(target)))
    throw new Error('Crie antes o diretório privado do comprovante.');
  return target;
}

export async function cleanInstall() {
  const root = process.cwd(),
    id = randomUUID(),
    directory = resolve('.local', `clean08-${id}`),
    container = `radar-validation-${id}`;
  const runtime = cleanInstallRuntime(process.env, root);
  const resultPath = cleanInstallResultPath(process.env, root);
  let runtimeVerification = null;
  const identity = sourceIdentity(),
    results = [],
    children = [];
  let created = false;
  const env = {
    ...process.env,
    POSTGRES_USER: 'radar_validation',
    POSTGRES_DB: 'radar_validation',
    POSTGRES_PASSWORD: randomBytes(32).toString('hex'),
    NODE_ENV: 'development',
    ALLOW_INSECURE_LOCAL_HTTP: 'true',
    BOOTSTRAP_EMAIL: 'clean@example.invalid',
    BOOTSTRAP_PASSWORD: `Synthetic-${randomBytes(24).toString('hex')}`,
    NEXT_TELEMETRY_DISABLED: '1',
    RETENTION_JOBS_ENABLED: 'false',
    RADAR_E2E_BUILD: 'false',
  };
  delete env.UV_PROJECT_ENVIRONMENT;
  if (runtime.requested === 'PYTHON313_SIGNED') {
    env.PYTHONPATH = resolve(directory, 'services/edge/src');
  }
  async function port() {
    const s = createServer();
    await new Promise((r) => s.listen(0, '127.0.0.1', r));
    const p = s.address().port;
    await new Promise((r) => s.close(r));
    return p;
  }
  function run(name, command, args, input) {
    const log = openSync(resolve(directory, '.local', `${name}.log`), 'w');
    const r = spawnSync(command, args, {
      cwd: directory,
      env,
      input,
      stdio: [input === undefined ? 'ignore' : 'pipe', log, log],
      windowsHide: true,
    });
    closeSync(log);
    results.push({ name, exitCode: r.status });
    if (r.status !== 0)
      throw new Error(`Instalação limpa: ${name} falhou; consulte log privado na cópia.`);
    console.log(`Instalação limpa: ${name} aprovado.`);
  }
  function pnpm(name, args) {
    const old = env.NODE_ENV;
    if (name === 'build') env.NODE_ENV = 'production';
    try {
      run(name, process.execPath, [process.env.npm_execpath, ...args]);
    } finally {
      env.NODE_ENV = old;
    }
  }
  function start(name, args) {
    const log = openSync(resolve(directory, '.local', `${name}.log`), 'w');
    const p = spawn(process.execPath, args, {
      cwd: directory,
      env: name === 'web' ? { ...env, NODE_ENV: 'production' } : env,
      stdio: ['ignore', log, log],
      windowsHide: true,
    });
    p.once('error', () => {});
    children.push(p);
    closeSync(log);
    return p;
  }
  async function ready(url, child) {
    for (let i = 0; i < 100; i++) {
      if (child.exitCode !== null) throw new Error('Processo limpo encerrou.');
      try {
        if ((await fetch(url, { signal: AbortSignal.timeout(1000) })).ok) return;
      } catch {
        /* wait only owned process */
      }
      await new Promise((r) => setTimeout(r, 500));
    }
    throw new Error('Processo limpo não ficou pronto.');
  }
  try {
    mkdirSync(resolve(directory, '.local'), { recursive: true });
    if (runtime.requested === 'PYTHON313_SIGNED') {
      const verificationOutput = resolve('.local', `clean08-runtime-${id}`);
      const verificationLog = resolve(directory, '.local/runtime-verification.log');
      const fd = openSync(verificationLog, 'wx');
      let verification;
      try {
        verification = spawnSync(
          'powershell',
          [
            '-NoProfile',
            '-File',
            resolve(root, 'scripts/validation/prepare-python313.ps1'),
            '-ExistingRuntime',
            dirname(runtime.python),
            '-SkipSync',
            '-Output',
            verificationOutput,
          ],
          { cwd: root, env, stdio: ['ignore', fd, fd], windowsHide: true },
        );
      } finally {
        closeSync(fd);
      }
      results.push({ name: 'signed-runtime-verification', exitCode: verification.status });
      if (verification.status !== 0)
        throw new Error(
          'Runtime PSF não verificado; confira o log privado. Nenhum uv/Python alternativo foi solicitado.',
        );
      const receiptPath = resolve(verificationOutput, 'preparation.json');
      const receipt = JSON.parse(readFileSync(receiptPath, 'utf8').replace(/^\uFEFF/, ''));
      if (
        receipt.status !== 'RUNTIME_VERIFIED_SYNC_SKIPPED' ||
        resolve(receipt.python) !== runtime.python
      )
        throw new Error('Comprovante de runtime incompatível.');
      runtimeVerification = {
        path: receiptPath,
        status: receipt.status,
        patchLimitation: receipt.patchLimitation,
      };
    }
    const files = execFileSync(
      'git',
      ['ls-files', '--cached', '--others', '--exclude-standard', '-z'],
      { encoding: 'utf8' },
    )
      .split('\0')
      .filter(Boolean);
    for (const file of files) {
      const dest = resolve(directory, file);
      mkdirSync(dirname(dest), { recursive: true });
      copyFileSync(resolve(root, file), dest);
    }
    // Explicit external prerequisites: exact Node/pnpm/uv binaries in PATH, Docker,
    // cached Docker image and optional package caches. No original .local or .env copied.
    pnpm('install', ['install', '--frozen-lockfile']);
    run('uv-sync', 'uv', runtime.syncArguments);
    docker(
      [
        'create',
        '--name',
        container,
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
        '127.0.0.1::5432',
        'postgres:17.11',
      ],
      undefined,
      { env },
    );
    created = true;
    docker(['start', container]);
    let healthy = false;
    for (let i = 0; i < 60; i++) {
      if (
        spawnSync(
          'docker',
          [
            'exec',
            container,
            'pg_isready',
            '-h',
            '127.0.0.1',
            '-U',
            env.POSTGRES_USER,
            '-d',
            env.POSTGRES_DB,
          ],
          { windowsHide: true },
        ).status === 0
      ) {
        healthy = true;
        break;
      }
      await new Promise((r) => setTimeout(r, 500));
    }
    if (!healthy) throw new Error('Banco limpo indisponível.');
    const pgPort = docker(['port', container, '5432/tcp']).match(/^127\.0\.0\.1:(\d+)$/)?.[1];
    if (!pgPort || ['5432', '15432'].includes(pgPort)) throw new Error('Porta não isolada.');
    const apiPort = await port(),
      webPort = await port();
    if (apiPort === webPort) throw new Error('Portas colidiram; execute novamente.');
    env.DATABASE_URL = `postgresql://${env.POSTGRES_USER}:${env.POSTGRES_PASSWORD}@127.0.0.1:${pgPort}/${env.POSTGRES_DB}`;
    env.API_HOST = '127.0.0.1';
    env.API_PORT = String(apiPort);
    env.WEB_ORIGIN = `http://127.0.0.1:${webPort}`;
    env.API_INTERNAL_URL = `http://127.0.0.1:${apiPort}/v1`;
    writeFileSync(
      resolve(directory, '.env'),
      `POSTGRES_USER=${env.POSTGRES_USER}\nPOSTGRES_DB=${env.POSTGRES_DB}\nPOSTGRES_PASSWORD=${env.POSTGRES_PASSWORD}\nPOSTGRES_PORT=${pgPort}\n`,
      { mode: 0o600 },
    );
    pnpm('setup-env', ['setup:env']);
    pnpm('build', ['build']);
    pnpm('migrate', ['db:migrate']);
    pnpm('seed', ['--filter', '@radar/api', 'db:seed']);
    run('model-fetch', 'uv', [
      ...runtime.runArguments,
      ...(runtime.requested === 'PYTHON313_SIGNED'
        ? ['python', 'scripts/run-edge.py']
        : ['radar-edge']),
      'model-fetch',
      '--variant',
      'full',
    ]);
    run('worker', 'uv', [
      ...runtime.runArguments,
      'python',
      '-c',
      `
import cv2, json, numpy as np
from pathlib import Path
from radar_edge.config import EdgeConfig
from radar_edge.pipeline import doctor, run_pipeline
from radar_edge.calibration import calibrate
path=Path('.local/infrastructure.avi')
writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10,(320,240))
assert writer.isOpened()
for index in range(30): writer.write(np.full((240,320,3),100+index,dtype=np.uint8))
writer.release()
c=EdgeConfig.model_validate({'cameraId':'11111111-1111-4111-8111-111111111111','source':{'kind':'FILE','path':str(path),'videoId':'synthetic-clean','authorized':True},'model':{'variant':'full','path':'.local/models/pose_landmarker_full.task'},'calibrationPath':'.local/calibration-clean.json'})
assert doctor(c)['inferenceExecuted']
Path('.local/points.json').write_text(json.dumps([[0.05,0.05],[0.95,0.05],[0.95,0.95],[0.05,0.95]]))
calibrate(c,0,'.local/points.json',True)
report,code=run_pipeline(c)
assert code==0 and report['metrics']['analyzedFrames']>0
print(json.dumps({'status':'ok','material':'SYNTHETIC_NO_PERSON','model':report['model'],'analyzedFrames':report['metrics']['analyzedFrames']}))
`,
    ]);
    const api = start('api', ['apps/api/dist/main.js']);
    await ready(`${env.API_INTERNAL_URL}/health/ready`, api);
    const web = start('web', [
      'apps/web/node_modules/next/dist/bin/next',
      'start',
      'apps/web',
      '--hostname',
      '127.0.0.1',
      '--port',
      String(webPort),
    ]);
    await ready(`${env.WEB_ORIGIN}/login`, web);
    const login = await fetch(`${env.WEB_ORIGIN}/api/auth/login`, {
      method: 'POST',
      headers: { Origin: env.WEB_ORIGIN, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: env.BOOTSTRAP_EMAIL, password: env.BOOTSTRAP_PASSWORD }),
    });
    if (login.status !== 200) throw new Error('Login pelo proxy limpo falhou.');
    results.push({ name: 'api-web-proxy-login', exitCode: 0 });
    writeFileSync(
      resultPath,
      JSON.stringify(
        {
          status: 'ok',
          identity,
          directory,
          results,
          requestedRuntime: runtime.requested,
          pythonProject: runtime.project,
          signedPythonExecutable: runtime.python,
          runtimeVerification,
          prerequisites:
            runtime.requested === 'PYTHON313_SIGNED'
              ? 'Windows x64; exact activated Node/pnpm/uv; Docker Desktop/postgres:17.11; existing official PSF 3.13.17 runtime verified by pinned hashes and Authenticode before execution; no Python downloads; package caches reused when available; internet available for package/model preparation'
              : 'Windows x64; exact activated Node/pnpm/uv; Docker Desktop/postgres:17.11; Python downloaded via uv if missing; package caches reused when available; internet available for preparation',
          originalPrivateFilesCopied: false,
          perceptionProven: false,
          offlineProven: false,
        },
        null,
        2,
      ),
      process.env.RADAR_CLEAN_INSTALL_RESULT ? { flag: 'wx' } : undefined,
    );
    console.log('Instalação limpa aprovada; não comprova percepção nem ausência de internet.');
  } finally {
    for (const child of children.reverse()) {
      if (child.exitCode === null) {
        child.kill();
        await Promise.race([
          new Promise((r) => child.once('exit', r)),
          new Promise((r) => setTimeout(r, 3000)),
        ]);
      }
    }
    if (created) docker(['rm', '-f', '-v', container]);
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await cleanInstall();
}
