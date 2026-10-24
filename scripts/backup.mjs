import { spawnSync } from 'node:child_process';
import { randomBytes, randomUUID, createHash } from 'node:crypto';
import {
  mkdirSync,
  readFileSync,
  writeFileSync,
  realpathSync,
  lstatSync,
  existsSync,
} from 'node:fs';
import { resolve, dirname, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const root = resolve(fileURLToPath(new URL('../', import.meta.url)));
export function privatePath(value) {
  const p = resolve(root, value),
    base = resolve(root, '.local');
  if (p === base || !p.startsWith(base + sep)) throw new Error('Use um subdiretório de .local.');
  for (let at = p; at !== root; at = dirname(at)) {
    if (existsSync(at) && (lstatSync(at).isSymbolicLink() || realpathSync(at) !== at))
      throw new Error('Links e redirecionamentos não são aceitos no backup.');
  }
  return p;
}
export function docker(args, input, extra = {}) {
  const r = spawnSync('docker', args, { encoding: 'utf8', input, windowsHide: true, ...extra });
  if (r.status !== 0) throw new Error('Comando Docker falhou; detalhes privados foram omitidos.');
  return r.stdout.trim();
}
const hash = (path) => createHash('sha256').update(readFileSync(path)).digest('hex');
function identity(container) {
  if (!/^(radar-postgres-1|radar-(test|restore|validation)-[a-f0-9-]{12,36})$/.test(container))
    throw new Error('Container fora do escopo do Radar.');
  const item = JSON.parse(docker(['inspect', container]))[0];
  if (item.Config.Image !== 'postgres:17.11') throw new Error('Exige PostgreSQL 17.11.');
  const values = Object.fromEntries(
    item.Config.Env.map((s) => {
      const i = s.indexOf('=');
      return [s.slice(0, i), s.slice(i + 1)];
    }),
  );
  const user = values.POSTGRES_USER,
    db = values.POSTGRES_DB;
  if (![user, db].every((s) => /^[a-zA-Z0-9_]+$/.test(s ?? '')))
    throw new Error('Identidade de banco inválida.');
  return { user, db };
}
export function sql(container, text) {
  const { user, db } = identity(container);
  return docker(
    ['exec', '-i', container, 'psql', '-X', '-qAt', '-v', 'ON_ERROR_STOP=1', '-U', user, '-d', db],
    text,
  );
}
export async function createBackup({ container = 'radar-postgres-1', output, stopped = false }) {
  if (!stopped)
    throw new Error('Pare API, web e workers e informe --stopped; banco permanece ligado.');
  const dir = privatePath(output ?? `.local/backups/${randomUUID()}`);
  if (existsSync(dir)) throw new Error('Destino já existe; nenhuma cópia foi sobrescrita.');
  const { user, db } = identity(container);
  const clients = Number(
    sql(
      container,
      "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND backend_type='client backend' AND pid<>pg_backend_pid();",
    ),
  );
  if (clients) throw new Error('Há conexões ativas no banco; pare os processos e tente novamente.');
  mkdirSync(dir, { recursive: true });
  const temp = `/tmp/radar-backup-${randomUUID()}.dump`;
  try {
    docker([
      'exec',
      container,
      'pg_dump',
      '-U',
      user,
      '-d',
      db,
      '--format=custom',
      '--no-owner',
      '--no-acl',
      '-f',
      temp,
    ]);
    docker(['cp', `${container}:${temp}`, resolve(dir, 'database.dump')]);
    const createdAt = new Date();
    const meta = {
      schemaVersion: 1,
      status: 'complete',
      postgres: '17.11',
      createdAt: createdAt.toISOString(),
      expiresAt: new Date(+createdAt + 7 * 86400000).toISOString(),
      databaseSha256: hash(resolve(dir, 'database.dump')),
      mediaIncluded: false,
      secrets:
        'Contains account hashes and retained database evidence; private, unencrypted. No environment files or bearer tokens copied.',
      processesStoppedAsserted: true,
    };
    writeFileSync(resolve(dir, 'backup.json'), JSON.stringify(meta, null, 2) + '\n', {
      flag: 'wx',
      mode: 0o600,
    });
    return { status: 'ok', directory: relative(root, dir), ...meta };
  } finally {
    docker(['exec', container, 'rm', '-f', temp]);
  }
}
export async function restoreBackup({ backup }) {
  const dir = privatePath(backup),
    dump = privatePath(resolve(dir, 'database.dump'));
  const manifest = JSON.parse(readFileSync(resolve(dir, 'backup.json'), 'utf8'));
  if (
    manifest.schemaVersion !== 1 ||
    manifest.status !== 'complete' ||
    manifest.mediaIncluded !== false ||
    manifest.databaseSha256 !== hash(dump)
  )
    throw new Error('Backup inválido ou hash divergente.');
  if (
    !Number.isFinite(Date.parse(manifest.expiresAt)) ||
    Date.parse(manifest.expiresAt) <= Date.now()
  )
    throw new Error('Backup expirado; preserve a política de sete dias.');
  const id = randomUUID(),
    container = `radar-restore-${id}`,
    password = randomBytes(32).toString('hex');
  const env = {
    ...process.env,
    POSTGRES_USER: 'radar_restore',
    POSTGRES_DB: 'radar_restore',
    POSTGRES_PASSWORD: password,
  };
  let created = false;
  try {
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
    let ready = false;
    for (let i = 0; i < 60; i++) {
      const probe = spawnSync(
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
      );
      if (probe.status === 0) {
        ready = true;
        break;
      }
      await new Promise((r) => setTimeout(r, 500));
    }
    if (!ready) throw new Error('Restore não ficou pronto.');
    docker(['cp', dump, `${container}:/tmp/restore.dump`]);
    docker([
      'exec',
      container,
      'pg_restore',
      '-U',
      env.POSTGRES_USER,
      '-d',
      env.POSTGRES_DB,
      '--no-owner',
      '--no-acl',
      '--exit-on-error',
      '/tmp/restore.dump',
    ]);
    docker(['exec', container, 'rm', '-f', '/tmp/restore.dump']);
    // No application is running here. Revoke authority and redact BEFORE opening HTTP.
    sql(
      container,
      `BEGIN;
      UPDATE "Session" SET "revokedAt"=CURRENT_TIMESTAMP WHERE "revokedAt" IS NULL;
      UPDATE "DeviceCredential" SET "revokedAt"=CURRENT_TIMESTAMP WHERE "revokedAt" IS NULL;
      UPDATE "Camera" SET "evidenceMode"='skeleton',"snapshotAuthorizedAt"=NULL,"expectedRunning"=false,"activeRunId"=NULL,"lastHeartbeat"=NULL,"heartbeatReceivedAt"=NULL,"heartbeatSequence"=NULL;
      UPDATE "Evidence" SET state=CASE WHEN state='DELETED' THEN 'DELETED' ELSE 'EXPIRED' END,"deletedAt"=COALESCE("deletedAt",CURRENT_TIMESTAMP),"objectKey"=NULL,bytes=0;
      UPDATE "Incident" SET pose=NULL,"poseRedactedAt"=COALESCE("poseRedactedAt",CURRENT_TIMESTAMP) WHERE "receivedAt"<=CURRENT_TIMESTAMP-INTERVAL '7 days';
      UPDATE "EventReceipt" SET payload=NULL,"redactedAt"=COALESCE("redactedAt",CURRENT_TIMESTAMP) WHERE "receivedAt"<=CURRENT_TIMESTAMP-INTERVAL '7 days';
      INSERT INTO "AuditEntry" (id,"tenantId",action,"createdAt","resultCode") SELECT gen_random_uuid(),id,'RESTORE_SANITIZED',CURRENT_TIMESTAMP,'MEDIA_EXCLUDED' FROM "Tenant";
      COMMIT;`,
    );
    const binding = docker(['port', container, '5432/tcp']);
    const port = binding.match(/^127\.0\.0\.1:(\d+)$/)?.[1];
    if (!port || ['5432', '15432'].includes(port)) throw new Error('Porta de restore inválida.');
    const restored = privatePath(`.local/restores/${id}`);
    mkdirSync(restored, { recursive: true });
    const config = {
      container,
      databaseUrl: `postgresql://radar_restore:${password}@127.0.0.1:${port}/radar_restore`,
      evidenceDirectory: `.local/restores/${id}/evidence`,
      sendingEnabled: false,
      createdAt: new Date().toISOString(),
    };
    const retained = spawnSync(process.execPath, ['apps/api/dist/cli.js', 'retention'], {
      cwd: root,
      env: {
        ...process.env,
        DATABASE_URL: config.databaseUrl,
        NODE_ENV: 'development',
        ALLOW_INSECURE_LOCAL_HTTP: 'true',
        WEB_ORIGIN: 'http://127.0.0.1:3000',
        LOCAL_DATA_DIR: config.evidenceDirectory,
        RETENTION_JOBS_ENABLED: 'false',
      },
      encoding: 'utf8',
      windowsHide: true,
    });
    if (retained.status !== 0)
      throw new Error(
        'Retenção do restore falhou; nenhum acesso foi liberado. Compile a API antes.',
      );
    writeFileSync(resolve(restored, 'restore-private.json'), JSON.stringify(config, null, 2), {
      mode: 0o600,
      flag: 'wx',
    });
    return {
      status: 'ok',
      container,
      directory: relative(root, restored),
      sessionsRevoked: true,
      deviceCredentialsRevoked: true,
      mediaExpired: true,
      sendingEnabled: false,
    };
  } catch (error) {
    if (created) docker(['rm', '-f', '-v', container]);
    throw error;
  }
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const { values, positionals } = parseArgs({
      options: {
        container: { type: 'string' },
        output: { type: 'string' },
        backup: { type: 'string' },
        stopped: { type: 'boolean' },
      },
      allowPositionals: true,
    });
    const result =
      positionals[0] === 'create'
        ? await createBackup(values)
        : positionals[0] === 'restore' && values.backup
          ? await restoreBackup(values)
          : null;
    if (!result) throw new Error('Use create --stopped ou restore --backup .local/backups/<id>.');
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
