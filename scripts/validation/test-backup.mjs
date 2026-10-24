import assert from 'node:assert/strict';
import { randomUUID, randomBytes } from 'node:crypto';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { docker, createBackup, restoreBackup, sql } from '../backup.mjs';
import { createApplication } from '../../apps/api/dist/application.js';
import { createDatabase } from '../../apps/api/dist/database.js';
import { seed } from '../../apps/api/dist/bootstrap.js';
const requireApi = createRequire(new URL('../../apps/api/package.json', import.meta.url));
const request = requireApi('supertest');
const sharp = requireApi('sharp');
const id = randomUUID(),
  source = `radar-validation-${id}`;
const dir = `.local/etapa08/backup-test-${id}`;
const env = {
  ...process.env,
  POSTGRES_USER: 'radar_validation',
  POSTGRES_DB: 'radar_validation',
  POSTGRES_PASSWORD: randomBytes(32).toString('hex'),
};
const password = `Synthetic-${randomBytes(20).toString('hex')}`,
  origin = 'http://127.0.0.1:3000';
let app,
  db,
  restored,
  created = false;
const settings = (url, directory) => ({
  databaseUrl: url,
  host: '127.0.0.1',
  port: 3001,
  webOrigin: origin,
  secureCookie: false,
  localDataDir: resolve(directory),
  retentionEnabled: false,
});
const start = async (url, directory) => {
  ({ app } = await createApplication(settings(url, directory), false, {
    notificationsEnabled: false,
  }));
  await app.listen(0, '127.0.0.1');
  return request(app.getHttpServer());
};
const migrate = (url) => {
  const r = spawnSync(
    process.execPath,
    [process.env.npm_execpath, '--filter', '@radar/api', 'db:migrate'],
    { env: { ...env, DATABASE_URL: url }, encoding: 'utf8', windowsHide: true },
  );
  assert.equal(r.status, 0, 'Migrações no banco isolado');
};
try {
  mkdirSync(dir, { recursive: true });
  docker(
    [
      'create',
      '--name',
      source,
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
  docker(['start', source]);
  let ready = false;
  for (let i = 0; i < 60; i++) {
    if (
      spawnSync(
        'docker',
        [
          'exec',
          source,
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
      ready = true;
      break;
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  assert.ok(ready);
  const port = docker(['port', source, '5432/tcp']).match(/^127\.0\.0\.1:(\d+)$/)?.[1];
  assert.ok(port && !['5432', '15432'].includes(port));
  const url = `postgresql://${env.POSTGRES_USER}:${env.POSTGRES_PASSWORD}@127.0.0.1:${port}/${env.POSTGRES_DB}`;
  migrate(url);
  db = createDatabase(url);
  const account = await seed(db, {
    email: 'backup@example.invalid',
    password,
    tenantSlug: 'backup-test',
  });
  const camera = await db.camera.create({
    data: {
      tenantId: account.tenantId,
      siteId: account.siteId,
      name: 'Backup sintético',
      type: 'FILE',
      evidenceMode: 'snapshot',
      snapshotAuthorizedAt: new Date(Date.now() - 60000),
      device: { create: {} },
    },
  });
  let api = await start(url, `${dir}/source-evidence`);
  const login = await api
    .post('/v1/auth/login')
    .set('Origin', origin)
    .send({ email: 'backup@example.invalid', password });
  assert.equal(login.status, 200);
  const cookie = login.headers['set-cookie'][0].split(';')[0];
  const cred = await api
    .post(`/v1/cameras/${camera.id}/device-credentials`)
    .set('Cookie', cookie)
    .set('Origin', origin)
    .send({});
  assert.equal(cred.status, 201);
  const event = {
    ...JSON.parse(readFileSync('packages/contracts/fixtures/event-simulated.json', 'utf8')),
    eventId: randomUUID(),
    episodeId: randomUUID(),
    cameraId: camera.id,
    runId: randomUUID(),
    occurredAt: new Date(Date.now() - 2000).toISOString(),
    detectedAt: new Date().toISOString(),
    evidenceMode: 'snapshot',
    pose: [{ index: 23, x: 0.5, y: 0.5, visibility: 1 }],
  };
  const received = await api
    .post('/v1/edge/events')
    .set('Authorization', `Bearer ${cred.body.token}`)
    .send(event);
  assert.equal(received.status, 201);
  const jpeg = await sharp({
    create: { width: 32, height: 32, channels: 3, background: '#225533' },
  })
    .jpeg()
    .toBuffer();
  assert.equal(
    (
      await api
        .post(`/v1/edge/events/${event.eventId}/snapshot`)
        .set('Authorization', `Bearer ${cred.body.token}`)
        .set('Content-Type', 'image/jpeg')
        .send(jpeg)
    ).status,
    201,
  );
  const old = new Date(Date.now() - 8 * 86400000);
  await db.incident.update({ where: { id: received.body.incidentId }, data: { receivedAt: old } });
  await db.eventReceipt.updateMany({
    where: { eventId: event.eventId },
    data: { receivedAt: old },
  });
  const receiptHash = (
    await db.eventReceipt.findFirstOrThrow({ where: { eventId: event.eventId } })
  ).payloadHash;
  await app.close();
  app = null;
  await db.$disconnect();
  db = null;
  await assert.rejects(createBackup({ container: source, output: `${dir}/refused` }), /stopped/);
  const backup = await createBackup({ container: source, output: `${dir}/copy`, stopped: true });
  assert.equal(backup.mediaIncluded, false);
  restored = await restoreBackup({ backup: backup.directory });
  const privateConfig = JSON.parse(
    readFileSync(resolve(restored.directory, 'restore-private.json'), 'utf8'),
  );
  migrate(privateConfig.databaseUrl);
  db = createDatabase(privateConfig.databaseUrl);
  assert.equal(await db.user.count(), 1);
  assert.equal(await db.site.count(), 1);
  assert.equal(await db.camera.count(), 1);
  assert.equal(await db.incident.count(), 1);
  const incident = await db.incident.findUniqueOrThrow({ where: { id: received.body.incidentId } });
  assert.equal(incident.pose, null);
  assert.equal(incident.status, 'OPEN');
  const receipt = await db.eventReceipt.findFirstOrThrow({ where: { eventId: event.eventId } });
  assert.equal(receipt.payload, null);
  assert.equal(receipt.payloadHash, receiptHash);
  assert.equal(await db.session.count({ where: { revokedAt: null } }), 0);
  assert.equal(await db.deviceCredential.count({ where: { revokedAt: null } }), 0);
  const evidence = await db.evidence.findUniqueOrThrow({ where: { incidentId: incident.id } });
  assert.equal(evidence.state, 'EXPIRED');
  assert.equal(evidence.objectKey, null);
  assert.equal(evidence.bytes, 0);
  api = await start(privateConfig.databaseUrl, privateConfig.evidenceDirectory);
  assert.equal((await api.get('/v1/health/ready')).status, 200);
  assert.equal((await api.get('/v1/auth/me').set('Cookie', cookie)).status, 401);
  assert.equal(
    (
      await api
        .post('/v1/edge/events')
        .set('Authorization', `Bearer ${cred.body.token}`)
        .send(event)
    ).status,
    401,
  );
  const relogin = await api
    .post('/v1/auth/login')
    .set('Origin', origin)
    .send({ email: 'backup@example.invalid', password });
  assert.equal(relogin.status, 200);
  const restoredCookie = relogin.headers['set-cookie'][0].split(';')[0];
  assert.equal(
    (await api.get(`/v1/incidents/${incident.id}/snapshot`).set('Cookie', restoredCookie)).status,
    410,
  );
  const newCred = await api
    .post(`/v1/cameras/${camera.id}/device-credentials`)
    .set('Cookie', restoredCookie)
    .set('Origin', origin)
    .send({});
  assert.equal(newCred.status, 201);
  const duplicate = await api
    .post('/v1/edge/events')
    .set('Authorization', `Bearer ${newCred.body.token}`)
    .send(event);
  assert.equal(duplicate.status, 200);
  assert.equal(duplicate.body.duplicate, true);
  assert.equal(duplicate.body.incidentId, incident.id);
  assert.equal(await db.incident.count(), 1);
  assert.equal(await db.auditEntry.count({ where: { action: 'RESTORE_SANITIZED' } }), 1);
  assert.equal(
    sql(
      restored.container,
      "SELECT count(*) FROM pg_constraint WHERE contype='f' AND NOT convalidated;",
    ),
    '0',
  );
  const result = {
    status: 'ok',
    fixture: 'SYNTHETIC_NO_PERSON',
    checks: [
      'fresh database migration',
      'stopped backup',
      'dump SHA-256',
      'isolated restore',
      'relationships',
      'reapply migrations',
      'readiness',
      'login',
      'session and device revocation',
      'snapshot excluded/410',
      'pose and receipt redaction',
      'immutable deduplication after restore',
      'restore audit',
    ],
    originalDemoModified: false,
  };
  writeFileSync(`${dir}/result.json`, JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
} finally {
  await app?.close();
  await db?.$disconnect();
  if (restored) docker(['rm', '-f', '-v', restored.container]);
  if (created) docker(['rm', '-f', '-v', source]);
}
