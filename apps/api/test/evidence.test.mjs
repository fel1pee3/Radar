import { spawn } from 'node:child_process';
import 'reflect-metadata';
import { beforeAll, afterAll, test, expect } from '@jest/globals';
import request from 'supertest';
import sharp from 'sharp';
import { randomBytes, randomUUID, createHash } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createApplication } from '../dist/application.js';
import { readSettings } from '../dist/config.js';
import { createDatabase } from '../dist/database.js';
import { seed, createOperator } from '../dist/bootstrap.js';
import { tokenHash } from '../dist/security.js';
import { EvidenceService } from '../dist/evidence.js';

const dbUrl = new URL(process.env.DATABASE_URL ?? '');
if (
  !/^radar-test-[a-f0-9]{12}$/.test(process.env.RADAR_TEST_CONTAINER ?? '') ||
  ['5432', '15432', ''].includes(dbUrl.port)
)
  throw new Error('Use harness isolado.');
const origin = 'http://127.0.0.1:3000';
const directory = resolve('../../.local/etapa07/api', randomUUID());
const logs = [];
const logger = Object.fromEntries(
  ['log', 'error', 'warn', 'debug', 'verbose', 'fatal'].map((k) => [
    k,
    (...v) => logs.push(JSON.stringify(v)),
  ]),
);
const fakeSecret = 'FICTITIOUS-SECRET-MUST-NEVER-APPEAR-78429';
let db, app, api, owner, operator, other, camera, camera2, token, token2, fixture, jpeg, second;
let now = new Date();
const clock = { now: () => new Date(now) };
const settings = { ...readSettings(), localDataDir: directory, retentionEnabled: false };
async function session(account, role = 'OWNER') {
  const user = await db.user.findFirstOrThrow({ where: { tenantId: account.tenantId, role } });
  const value = `ses_${randomBytes(32).toString('base64url')}`;
  const row = await db.session.create({
    data: {
      tenantId: user.tenantId,
      userId: user.id,
      tokenHash: tokenHash(value),
      expiresAt: new Date(Date.now() + 3600000),
    },
  });
  return { cookie: `radar_session=${value}`, row, user };
}
async function device(cam, version = 1) {
  const dev = await db.device.findFirstOrThrow({ where: { cameraId: cam.id } });
  const token = `dev_${randomBytes(32).toString('base64url')}`;
  await db.deviceCredential.create({
    data: { tenantId: cam.tenantId, deviceId: dev.id, tokenHash: tokenHash(token), version },
  });
  return token;
}
function event(extra = {}) {
  return {
    ...structuredClone(fixture),
    eventId: randomUUID(),
    episodeId: randomUUID(),
    cameraId: camera.id,
    runId: randomUUID(),
    occurredAt: new Date(now - 2000).toISOString(),
    detectedAt: now.toISOString(),
    evidenceMode: 'snapshot',
    ...extra,
  };
}
const human = (method, path, who = owner) =>
  api[method](path).set('Cookie', who.cookie).set('Origin', origin);
const send = (e, t = token) =>
  api.post('/v1/edge/events').set('Authorization', `Bearer ${t}`).send(e);
const upload = (e, bytes = jpeg, t = token) =>
  api
    .post(`/v1/edge/events/${e.eventId}/snapshot`)
    .set('Authorization', `Bearer ${t}`)
    .set('Content-Type', 'image/jpeg')
    .send(bytes);
async function create(e = event()) {
  const r = await send(e);
  expect([200, 201]).toContain(r.status);
  return { e, id: r.body.incidentId };
}
async function preference(mode = 'snapshot', authorized = true) {
  return human('patch', `/v1/cameras/${camera.id}/evidence-preference`).send({ mode, authorized });
}
beforeAll(async () => {
  db = createDatabase(dbUrl.href);
  fixture = JSON.parse(
    await readFile('../../packages/contracts/fixtures/event-simulated.json', 'utf8'),
  );
  fixture.pose = [
    { index: 11, x: 0.3, y: 0.4, visibility: 1 },
    { index: 23, x: 0.5, y: 0.5, visibility: 1 },
  ];
  const a = await seed(db, {
    tenantSlug: 'evidence-isolated',
    email: 'evidence@example.invalid',
    password: fakeSecret,
  });
  await createOperator(db, {
    tenantSlug: 'evidence-isolated',
    email: 'evidence-op@example.invalid',
    password: fakeSecret,
  });
  const b = await seed(db, {
    tenantSlug: 'evidence-other',
    email: 'evidence-other@example.invalid',
    password: fakeSecret,
  });
  owner = await session(a);
  operator = await session(a, 'OPERATOR');
  other = await session(b);
  camera = await db.camera.create({
    data: {
      tenantId: a.tenantId,
      siteId: a.siteId,
      name: 'Evidencia sintetica',
      type: 'FILE',
      device: { create: {} },
    },
  });
  camera2 = await db.camera.create({
    data: {
      tenantId: b.tenantId,
      siteId: b.siteId,
      name: 'Outro tenant',
      type: 'FILE',
      device: { create: {} },
    },
  });
  token = await device(camera);
  token2 = await device(camera2);
  ({ app } = await createApplication(settings, logger, { clock, notificationsEnabled: false }));
  await app.listen(0, '127.0.0.1');
  api = request(app.getHttpServer());
  jpeg = await sharp({ create: { width: 80, height: 60, channels: 3, background: '#228855' } })
    .withExif({ IFD0: { Copyright: fakeSecret } })
    .jpeg()
    .toBuffer();
  second = await sharp({ create: { width: 80, height: 60, channels: 3, background: '#885522' } })
    .jpeg()
    .toBuffer();
});
afterAll(async () => {
  await app?.close();
  await db?.$disconnect();
});

test('preferência exige proprietário, Origin e autorização; padrão skeleton/sem imagem', async () => {
  expect((await db.camera.findUnique({ where: { id: camera.id } })).evidenceMode).toBe('skeleton');
  expect(
    (
      await human('patch', `/v1/cameras/${camera.id}/evidence-preference`, operator).send({
        mode: 'snapshot',
        authorized: true,
      })
    ).status,
  ).toBe(403);
  expect(
    (
      await api
        .patch(`/v1/cameras/${camera.id}/evidence-preference`)
        .set('Cookie', owner.cookie)
        .send({ mode: 'snapshot', authorized: true })
    ).status,
  ).toBe(403);
  expect((await preference('snapshot', false)).status).toBe(422);
  const { e, id } = await create(event({ evidenceMode: 'skeleton' }));
  expect((await upload(e)).status).toBe(403);
  expect((await human('get', `/v1/incidents/${id}`)).body.snapshot.state).toBe('DISABLED');
  const denied = await create(event({ evidenceMode: 'snapshot' }));
  expect((await upload(denied.e)).status).toBe(403);
  expect((await human('get', `/v1/incidents/${denied.id}`)).body.snapshot.state).toBe('DISABLED');
  await preference('none');
  const n = await create(event({ evidenceMode: 'skeleton' }));
  expect((await db.incident.findUnique({ where: { id: n.id } })).pose).toEqual([]);
  expect((await db.eventReceipt.findFirst({ where: { incidentId: n.id } })).payload.pose).toEqual(
    [],
  );
  await preference();
  await send({ ...n.e, eventId: randomUUID() });
  expect(
    (await db.eventReceipt.findMany({ where: { incidentId: n.id } })).every(
      (r) => r.payload.pose.length === 0,
    ),
  ).toBe(true);
  expect(
    await db.auditEntry.count({
      where: { action: 'EVIDENCE_PREFERENCE_CHANGED', actorId: owner.user.id },
    }),
  ).toBe(2);
});
test('JPEG sintético após evento; bytes reais, EXIF removido, leitura privada e auditada', async () => {
  const { e, id } = await create();
  expect((await human('get', `/v1/incidents/${id}`)).body.snapshot.state).toBe('AWAITING');
  const result = await upload(e);
  expect(result.status).toBe(201);
  expect(result.body.hash).toBe(createHash('sha256').update(jpeg).digest('hex'));
  const response = await human('get', `/v1/incidents/${id}/snapshot`);
  expect(response.status).toBe(200);
  expect(response.headers['cache-control']).toBe('no-store');
  const metadata = await sharp(response.body).metadata();
  expect(metadata.format).toBe('jpeg');
  expect(metadata.exif).toBeUndefined();
  expect(response.body.includes(Buffer.from(fakeSecret))).toBe(false);
  expect((await human('get', `/v1/incidents/${id}/snapshot`, operator)).status).toBe(200);
  expect(
    await db.auditEntry.count({ where: { incidentId: id, action: 'SNAPSHOT_ACCESSED' } }),
  ).toBe(2);
  const r = await db.evidence.findUnique({ where: { incidentId: id } });
  expect((await api.get(`/${r.objectKey}`)).status).toBe(404);
});
test('inválidos, PNG disfarçado, excesso de bytes/dimensões e referências rejeitados', async () => {
  const { e } = await create();
  for (const bytes of [
    Buffer.from('<svg/>'),
    await sharp({ create: { width: 1, height: 1, channels: 3, background: 'red' } })
      .png()
      .toBuffer(),
    jpeg.subarray(0, 40),
  ])
    expect((await upload(e, bytes)).status).toBe(422);
  expect((await upload(e, Buffer.alloc(2 * 1024 * 1024 + 1, 65))).status).toBe(413);
  expect(
    (
      await api
        .post(`/v1/edge/events/${e.eventId}/snapshot`)
        .set('Authorization', `Bearer ${token}`)
        .set('Content-Type', 'image/jpeg')
        .set('Content-Encoding', 'gzip')
        .send(jpeg)
    ).status,
  ).toBe(415);
  const wide = await sharp({ create: { width: 1281, height: 2, channels: 3, background: 'red' } })
    .jpeg()
    .toBuffer();
  expect((await upload(e, wide)).status).toBe(422);
  const bomb = Buffer.from(jpeg);
  const sof = bomb.indexOf(Buffer.from([255, 192]));
  expect(sof).toBeGreaterThan(0);
  bomb.writeUInt16BE(65000, sof + 5);
  bomb.writeUInt16BE(65000, sof + 7);
  expect((await upload(e, bomb)).status).toBe(422);
  expect((await upload(e, jpeg, token2)).status).toBe(404);
  expect(
    (
      await api
        .post(`/v1/edge/events/${randomUUID()}/snapshot`)
        .set('Authorization', `Bearer ${token}`)
        .set('Content-Type', 'text/plain')
        .send(jpeg)
    ).status,
  ).toBe(404);
});
test('sem sessão, bearer humano inválido, tenant cruzado, sessão expirada e revogada', async () => {
  const { e, id } = await create();
  await upload(e);
  expect((await api.get(`/v1/incidents/${id}/snapshot`)).status).toBe(401);
  expect(
    (await api.get(`/v1/incidents/${id}/snapshot`).set('Authorization', `Bearer ${token}`)).status,
  ).toBe(401);
  expect((await human('get', `/v1/incidents/${id}/snapshot`, other)).status).toBe(404);
  const temp = await session({ tenantId: owner.user.tenantId });
  await db.session.update({ where: { id: temp.row.id }, data: { expiresAt: new Date(0) } });
  expect((await human('get', `/v1/incidents/${id}/snapshot`, temp)).status).toBe(401);
  await db.session.update({
    where: { id: temp.row.id },
    data: { expiresAt: new Date(Date.now() + 360000), revokedAt: new Date() },
  });
  expect((await human('get', `/v1/incidents/${id}/snapshot`, temp)).status).toBe(401);
});
test('upload idempotente, concorrência, conflito e outra chave do episódio sem segunda imagem', async () => {
  const { e, id } = await create();
  const results = await Promise.all([upload(e), upload(e)]);
  expect(results.map((r) => r.status)).toEqual([201, 201]);
  expect(results.filter((r) => r.body.duplicate)).toHaveLength(1);
  expect(await db.evidence.count({ where: { incidentId: id } })).toBe(1);
  expect((await upload(e, second)).status).toBe(409);
  const alternate = { ...e, eventId: randomUUID() };
  expect((await send(alternate)).body.incidentId).toBe(id);
  expect((await upload(alternate)).status).toBe(409);
});
test('OWNER exclui com auditoria; OPERATOR/CSRF impedidos, reenvio não ressuscita', async () => {
  const { e, id } = await create();
  await upload(e);
  expect((await human('delete', `/v1/incidents/${id}/snapshot`, operator)).status).toBe(403);
  expect(
    (
      await api
        .delete(`/v1/incidents/${id}/snapshot`)
        .set('Cookie', owner.cookie)
        .set('Origin', 'http://evil.invalid')
    ).status,
  ).toBe(403);
  expect((await human('delete', `/v1/incidents/${id}/snapshot`)).status).toBe(200);
  expect((await human('delete', `/v1/incidents/${id}/snapshot`)).status).toBe(200);
  expect((await upload(e)).status).toBe(410);
  expect((await human('get', `/v1/incidents/${id}/snapshot`)).status).toBe(410);
  expect((await db.incident.findUnique({ where: { id } })).status).toBe('OPEN');
  expect((await db.evidence.findUnique({ where: { incidentId: id } })).objectKey).toBeNull();
  expect(await db.auditEntry.count({ where: { incidentId: id, action: 'SNAPSHOT_DELETED' } })).toBe(
    1,
  );
});
test('falha de disco não perde incidente; órfão de commit interrompido é reconciliado', async () => {
  const { e, id } = await create();
  const service = app.get(EvidenceService);
  const original = service.write.bind(service);
  service.write = async (key, data) => {
    await original(key, data);
    throw new Error(fakeSecret);
  };
  expect((await upload(e)).status).toBe(503);
  expect((await db.incident.findUnique({ where: { id } })).status).toBe('OPEN');
  service.write = original;
  await service.reconcile();
  const refs = new Set(
    (await db.evidence.findMany({ where: { objectKey: { not: null } } })).map((r) => r.objectKey),
  );
  expect((await readdir(directory)).every((name) => refs.has(name))).toBe(true);
  expect((await upload(e)).status).toBe(201);
  const remove = service.removeFile.bind(service);
  service.removeFile = async () => {
    throw new Error(fakeSecret);
  };
  expect((await human('delete', `/v1/incidents/${id}/snapshot`)).status).toBe(503);
  expect((await upload(e)).status).toBe(410);
  service.removeFile = remove;
  await service.reconcile();
  expect((await db.evidence.findUnique({ where: { incidentId: id } })).objectKey).toBeNull();
});
test('arquivo ausente retorna indisponibilidade, não ausência definitiva; path traversal negado', async () => {
  const { e, id } = await create();
  await upload(e);
  const service = app.get(EvidenceService);
  const row = await db.evidence.findUniqueOrThrow({ where: { incidentId: id } });
  await db.evidence.update({ where: { id: row.id }, data: { objectKey: '../../private.jpg' } });
  expect((await human('get', `/v1/incidents/${id}/snapshot`)).status).toBe(503);
  await db.evidence.update({ where: { id: row.id }, data: { objectKey: row.objectKey } });
  await service.removeFile(row.objectKey);
  expect((await human('get', `/v1/incidents/${id}/snapshot`)).status).toBe(503);
  const repaired = await upload(e);
  expect(repaired.status).toBe(201);
  expect(repaired.body.duplicate).toBe(true);
  expect((await human('get', `/v1/incidents/${id}/snapshot`)).status).toBe(200);
  await human('delete', `/v1/incidents/${id}/snapshot`);
});
test('Python para API real: snapshot sintético, ACK perdido e retomada em outro processo', async () => {
  const outbox = `.local/etapa07/python-http/${randomUUID()}/outbox.sqlite`;
  const apiUrl = `http://127.0.0.1:${app.getHttpServer().address().port}/v1`;
  const run = (action) =>
    new Promise((resolveResult, reject) => {
      const child = spawn(
        'uv',
        [
          'run',
          '--project',
          'services/edge',
          '--frozen',
          'python',
          'services/edge/tests/evidence_api_probe.py',
          action,
        ],
        {
          cwd: resolve('../..'),
          windowsHide: true,
          env: {
            ...process.env,
            EDGE_TEST_CAMERA: camera.id,
            EDGE_TEST_OUTBOX: outbox,
            EDGE_API_URL: apiUrl,
            EDGE_DEVICE_TOKEN: token,
          },
          stdio: ['ignore', 'pipe', 'pipe'],
        },
      );
      let output = '';
      child.stdout.on('data', (b) => {
        output = (output + b).slice(-8000);
      });
      child.stderr.on('data', () => {});
      child.on('error', () => reject(new Error('Probe sint?tico indispon?vel.')));
      child.on('exit', (code) => {
        try {
          if (code !== 0) throw new Error();
          resolveResult(JSON.parse(output));
        } catch {
          reject(new Error('Probe sint?tico falhou, sem detalhes sens?veis.'));
        }
      });
    });
  const first = await run('emit');
  expect(first.status).toBe('DELIVERED');
  expect(first.snapshots[0].status).toBe('PENDING');
  const resumed = await run('deliver');
  expect(resumed.snapshots[0].status).toBe('DELIVERED');
  expect(resumed.snapshots[0].bytes).toBeNull();
  expect(resumed.eventId).toBe(first.eventId);
  expect(await db.incident.count({ where: { id: first.confirmation.incidentId } })).toBe(1);
  expect(
    (await human('get', `/v1/incidents/${first.confirmation.incidentId}/snapshot`)).status,
  ).toBe(200);
}, 30000);

test('concorrência entre leitura, exclusão e reenvio não ressuscita evidência', async () => {
  const { e, id } = await create();
  await upload(e);
  const results = await Promise.all([
    human('get', `/v1/incidents/${id}/snapshot`),
    human('delete', `/v1/incidents/${id}/snapshot`),
    upload(e),
  ]);
  expect([200, 410]).toContain(results[0].status);
  expect(results[1].status).toBe(200);
  expect([201, 410]).toContain(results[2].status);
  expect((await upload(e)).status).toBe(410);
  expect((await db.incident.findUnique({ where: { id } })).status).toBe('OPEN');
});
test('falha do banco após escrita deixa órfão recuperável e alerta preservado', async () => {
  const { e, id } = await create();
  const service = app.get(EvidenceService);
  const locked = service.locked.bind(service);
  service.locked = (fn) =>
    locked((tx) =>
      fn({
        ...tx,
        evidence: new Proxy(tx.evidence, {
          get(target, key) {
            if (key === 'update')
              return async () => {
                throw new Error(fakeSecret);
              };
            return Reflect.get(target, key);
          },
        }),
      }),
    );
  expect((await upload(e)).status).toBe(500);
  service.locked = locked;
  expect((await db.incident.findUnique({ where: { id } })).status).toBe('OPEN');
  await service.reconcile();
  expect((await upload(e)).status).toBe(201);
});

test('24h/7d controlados: expiração e redação de TODAS cópias, hash preservado após restart', async () => {
  const { e, id } = await create();
  await upload(e);
  const before = await db.eventReceipt.findFirstOrThrow({ where: { incidentId: id } });
  expect(before.payload.pose.length).toBeGreaterThan(0);
  now = new Date(now.getTime() + 86400001);
  expect((await human('get', `/v1/incidents/${id}/snapshot`)).status).toBe(410);
  await app.close();
  ({ app } = await createApplication(settings, logger, { clock, notificationsEnabled: false }));
  await app.listen(0, '127.0.0.1');
  api = request(app.getHttpServer());
  await app.get(EvidenceService).retain();
  expect((await db.evidence.findUnique({ where: { incidentId: id } })).objectKey).toBeNull();
  expect((await upload(e)).status).toBe(410);
  now = new Date(now.getTime() + 7 * 86400000);
  await app.get(EvidenceService).retain();
  await app.get(EvidenceService).retain();
  const after = await db.eventReceipt.findUnique({ where: { id: before.id } });
  expect(after.payload).toBeNull();
  expect(after.payloadHash).toBe(before.payloadHash);
  expect((await db.incident.findUnique({ where: { id } })).pose).toBeNull();
  expect((await send(e)).body.incidentId).toBe(id);
  expect((await send({ ...e, signals: { ...e.signals, analysisFps: 6 } })).status).toBe(409);
  const alternate = { ...e, eventId: randomUUID() };
  expect((await send(alternate)).body.incidentId).toBe(id);
  expect(
    (await db.eventReceipt.findFirst({ where: { eventId: alternate.eventId } })).payload.pose,
  ).toEqual([]);
  expect(
    (
      await human('post', `/v1/incidents/${id}/actions`).send({
        actionId: randomUUID(),
        expectedVersion: 1,
        action: 'RECOGNIZE',
      })
    ).status,
  ).toBe(200);
});
test('purga 30d somente opt-in; recibo 90d impede ressurreição por chave/episódio', async () => {
  const { e, id } = await create();
  now = new Date(now.getTime() + 31 * 86400000);
  await app.get(EvidenceService).retain();
  expect(await db.incident.findUnique({ where: { id } })).not.toBeNull();
  expect(
    (await human('patch', '/v1/retention-preference', operator).send({ enabled: true })).status,
  ).toBe(403);
  expect((await human('patch', '/v1/retention-preference').send({ enabled: true })).status).toBe(
    200,
  );
  await app.get(EvidenceService).retain();
  expect(await db.incident.findUnique({ where: { id } })).toBeNull();
  expect((await send(e)).body.code).toBe('EVENT_EXPIRED');
  expect(
    (await send({ ...e, eventId: randomUUID(), detectedAt: now.toISOString() })).body.code,
  ).toBe('EVENT_EXPIRED');
  const receipt = await db.eventReceipt.findFirst({ where: { eventId: e.eventId } });
  expect(receipt.payload).toBeNull();
  expect(receipt.expiredAt).not.toBeNull();
  now = new Date(now.getTime() + 60 * 86400000);
  await app.get(EvidenceService).retain();
  expect(await db.eventReceipt.findUnique({ where: { id: receipt.id } })).toBeNull();
  expect((await send(e)).body.code).toBe('EVENT_TOO_OLD');
});
test('logs de testes não contêm senha/token/EXIF/erros sensíveis fictícios', async () => {
  const output = logs.join('\n');
  for (const secret of [fakeSecret, token, token2, owner.cookie.split('=')[1]])
    expect(output.includes(secret)).toBe(false);
  console.log(
    JSON.stringify({
      evidenceTests: 'synthetic-only',
      secretScan: 'passed',
      directory: 'private',
      physicalCapture: false,
    }),
  );
});

test('logger técnico persistido é limitado, expira e não copia conteúdo sensível', async () => {
  const { TechnicalLogger } = await import('../dist/technical-logger.js');
  const dir = resolve(directory, 'logs');
  const { mkdir, writeFile, utimes, readdir, readFile } = await import('node:fs/promises');
  await mkdir(dir, { recursive: true });
  const old = resolve(dir, `technical-${randomUUID()}.log`);
  await writeFile(old, 'old');
  await utimes(old, new Date(0), new Date(0));
  const logger = new TechnicalLogger(dir, () => new Date());
  logger.error({ event: 'request_failed', status: 503, message: fakeSecret, Authorization: token });
  logger.log(fakeSecret);
  logger.cleanup();
  const files = await readdir(dir);
  expect(files).not.toContain(old.split(/[\\/]/).pop());
  const output = (await Promise.all(files.map((f) => readFile(resolve(dir, f), 'utf8')))).join('');
  expect(output.includes(fakeSecret)).toBe(false);
  expect(output.includes(token)).toBe(false);
  const large = resolve(dir, `technical-${randomUUID()}.log`);
  await writeFile(large, Buffer.alloc(10 * 1024 * 1024));
  logger.cleanup();
  const { stat } = await import('node:fs/promises');
  let bytes = 0;
  for (const f of await readdir(dir)) bytes += (await stat(resolve(dir, f))).size;
  expect(bytes).toBeLessThanOrEqual(10 * 1024 * 1024);
});

test('job habilitado executa retenção na inicialização com relógio controlado', async () => {
  const { e, id } = await create();
  await upload(e);
  now = new Date(now.getTime() + 86400001);
  await app.close();
  ({ app } = await createApplication({ ...settings, retentionEnabled: true }, logger, {
    clock,
    notificationsEnabled: false,
  }));
  await app.listen(0, '127.0.0.1');
  api = request(app.getHttpServer());
  const { RetentionJob } = await import('../dist/evidence.js');
  const job = app.get(RetentionJob);
  for (let i = 0; i < 300 && job.busy; i++) await new Promise((resolve) => setTimeout(resolve, 10));
  expect(job.busy).toBe(false);
  const row = await db.evidence.findUnique({ where: { incidentId: id } });
  expect(row.state).toBe('EXPIRED');
  expect(row.objectKey).toBeNull();
});
