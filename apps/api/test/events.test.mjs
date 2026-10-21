import 'reflect-metadata';
import { beforeAll, afterAll, beforeEach, test, expect } from '@jest/globals';
import request from 'supertest';
import { randomBytes, randomUUID } from 'node:crypto';
import { readFile, mkdtemp, writeFile, rm } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createApplication } from '../dist/application.js';
import { createDatabase } from '../dist/database.js';
import { readSettings } from '../dist/config.js';
import { seed, createOperator } from '../dist/bootstrap.js';
import { NotificationExecutor } from '../dist/notifications.js';
import { ContractPipe } from '../dist/event-support.js';

const url = new URL(process.env.DATABASE_URL ?? '');
if (
  url.hostname !== '127.0.0.1' ||
  ['5432', '15432', ''].includes(url.port) ||
  !/^\/radar_test_[a-f0-9]{12}$/.test(url.pathname) ||
  !/^radar-test-[a-f0-9]{12}$/.test(process.env.RADAR_TEST_CONTAINER ?? '')
) {
  throw new Error('Execute somente via pnpm.cmd test:api, com banco exclusivo de testes.');
}
const fixtures = JSON.parse(
  await readFile(
    new URL('../../../packages/contracts/fixtures/cases.json', import.meta.url),
    'utf8',
  ),
);
const sample = JSON.parse(
  await readFile(
    new URL('../../../packages/contracts/fixtures/event-simulated.json', import.meta.url),
    'utf8',
  ),
);
const heartbeatSample = fixtures.find((item) => item.name === 'heartbeat-v1-basic').value;
const database = createDatabase(url.href);
const origin = 'http://127.0.0.1:3000';
const password = `Synthetic-${randomBytes(18).toString('hex')}`;
const secrets = new Set([password, url.password, url.href]);
const logs = [];
const logger = Object.fromEntries(
  ['log', 'error', 'warn', 'debug', 'verbose', 'fatal'].map((level) => [
    level,
    (...args) => logs.push(JSON.stringify({ level, args })),
  ]),
);
const baseTime = new Date('2026-10-21T15:00:00.000Z');
let now = new Date(baseTime);
const clock = { now: () => new Date(now) };
let app,
  api,
  executor,
  a,
  b,
  ownerA,
  ownerB,
  operatorA,
  cameraA,
  cameraB,
  otherCamera,
  credentialA,
  credentialB;
const as = (cookie, method, path) => api[method](path).set('Cookie', cookie).set('Origin', origin);
const worker = (path, body, credential = credentialA) =>
  api.post(`/v1/edge/${path}`).set('Authorization', `Bearer ${credential.token}`).send(body);
const event = (overrides = {}) => ({
  ...structuredClone(sample),
  eventId: randomUUID(),
  episodeId: randomUUID(),
  runId: randomUUID(),
  cameraId: cameraA.id,
  occurredAt: new Date(now.getTime() - 2000).toISOString(),
  detectedAt: now.toISOString(),
  ...overrides,
});
const heartbeat = (overrides = {}) => ({
  ...structuredClone(heartbeatSample),
  cameraId: cameraA.id,
  runId: randomUUID(),
  sentAt: now.toISOString(),
  ...overrides,
});
const action = (incidentId, body, cookie = operatorA) =>
  as(cookie, 'post', `/v1/incidents/${incidentId}/actions`).send(body);
const command = (name, version = 1, extra = {}) => ({
  actionId: randomUUID(),
  expectedVersion: version,
  action: name,
  ...extra,
});
async function ingest(body = event(), credential = credentialA) {
  const response = await worker('events', body, credential);
  expect(response.status).toBe(201);
  return response.body;
}
async function detail(id, cookie = ownerA) {
  return as(cookie, 'get', `/v1/incidents/${id}`);
}
async function health() {
  const response = await as(ownerA, 'get', `/v1/cameras/${cameraA.id}`);
  expect(response.status).toBe(200);
  return response.body.health;
}
async function login(email) {
  const response = await api.post('/v1/auth/login').set('Origin', origin).send({ email, password });
  expect(response.status).toBe(200);
  const cookie = response.headers['set-cookie'][0].split(';')[0];
  secrets.add(cookie.split('=')[1]);
  return cookie;
}
async function createCamera(cookie, siteId) {
  const response = await as(cookie, 'post', '/v1/cameras').send({
    siteId,
    name: 'Contrato sintético',
    type: 'WEBCAM',
  });
  expect(response.status).toBe(201);
  return response.body;
}
async function issue(cookie, cameraId) {
  const response = await as(cookie, 'post', `/v1/cameras/${cameraId}/device-credentials`).send({});
  expect(response.status).toBe(201);
  secrets.add(response.body.token);
  return response.body;
}

beforeAll(async () => {
  ({ app } = await createApplication(readSettings(), logger, {
    clock,
    notificationsEnabled: false,
  }));
  await app.listen(0, '127.0.0.1');
  api = request(app.getHttpServer());
  executor = app.get(NotificationExecutor);
  a = await seed(database, {
    tenantSlug: 'events-a',
    email: 'events-owner-a@example.invalid',
    password,
  });
  b = await seed(database, {
    tenantSlug: 'events-b',
    email: 'events-owner-b@example.invalid',
    password,
  });
  await createOperator(database, {
    tenantSlug: 'events-a',
    email: 'events-operator@example.invalid',
    password,
  });
  ownerA = await login('events-owner-a@example.invalid');
  ownerB = await login('events-owner-b@example.invalid');
  operatorA = await login('events-operator@example.invalid');
  cameraA = await createCamera(ownerA, a.siteId);
  cameraB = await createCamera(ownerB, b.siteId);
  otherCamera = await createCamera(ownerA, a.siteId);
  credentialA = await issue(ownerA, cameraA.id);
  credentialB = await issue(ownerB, cameraB.id);
});
beforeEach(() => {
  now = new Date(baseTime);
});
afterAll(async () => {
  try {
    if (app) await app.close();
  } finally {
    await database.$disconnect();
  }
});

for (const fixture of fixtures) {
  test(`mesmo exemplo compartilhado na API: ${fixture.name}`, () => {
    const pipe = new ContractPipe(fixture.schema);
    if (fixture.valid) expect(pipe.transform(fixture.value)).toEqual(fixture.value);
    else expect(() => pipe.transform(fixture.value)).toThrow();
  });
}

test('HTTP aplica schemas fechados antes da persistência e limita o corpo a 64 KiB', async () => {
  const incident = await ingest();
  const before = await database.eventReceipt.count();
  for (const fixture of fixtures.filter((item) => !item.valid)) {
    const body = structuredClone(fixture.value);
    if (body.cameraId === sample.cameraId) body.cameraId = cameraA.id;
    const response =
      fixture.schema === 'incident-action-v1'
        ? await action(incident.incidentId, body)
        : await worker(fixture.schema === 'event-v1' ? 'events' : 'heartbeat', body);
    expect({ name: fixture.name, status: response.status }).toEqual({
      name: fixture.name,
      status: 422,
    });
  }
  expect(await database.eventReceipt.count()).toBe(before);
  expect((await worker('events', { ...event(), huge: 'a'.repeat(65536) })).status).toBe(413);
});

test('dez reenvios concorrentes e dez sequenciais: um incidente, um recibo, um aviso', async () => {
  const body = event();
  const results = await Promise.all(Array.from({ length: 10 }, () => worker('events', body)));
  expect(results.filter((response) => response.status === 201)).toHaveLength(1);
  expect(results.filter((response) => response.status === 200)).toHaveLength(9);
  const id = results[0].body.incidentId;
  for (let index = 0; index < 10; index++) {
    const response = await worker('events', body);
    expect(response.status).toBe(200);
    expect(response.body.incidentId).toBe(id);
  }
  expect(new Set(results.map((response) => response.body.incidentId)).size).toBe(1);
  expect(await database.eventReceipt.count({ where: { eventId: body.eventId } })).toBe(1);
  expect(
    await database.incident.count({ where: { cameraId: cameraA.id, episodeId: body.episodeId } }),
  ).toBe(1);
  expect(
    await database.auditEntry.count({ where: { incidentId: id, action: 'INCIDENT_CREATED' } }),
  ).toBe(1);
  await Promise.all([executor.drain(200), executor.drain(200)]);
  const intent = await database.notificationIntent.findUniqueOrThrow({
    where: { incidentId: id },
    include: { delivery: true },
  });
  expect(intent.status).toBe('DELIVERED');
  expect(intent.delivery.channel).toBe('SIMULATED');
  expect(intent.delivery.urgent).toBe(false);
  expect(await database.notificationDelivery.count({ where: { intentId: intent.id } })).toBe(1);
});

test('hash canônico aceita ordem diferente; conflitos não alteram original nem avisos', async () => {
  const body = event();
  const receipt = await ingest(body);
  const before = await detail(receipt.incidentId);
  function reverse(value) {
    return Array.isArray(value)
      ? value.map(reverse)
      : value && typeof value === 'object'
        ? Object.fromEntries(
            Object.entries(value)
              .reverse()
              .map(([key, item]) => [key, reverse(item)]),
          )
        : value;
  }
  expect((await worker('events', reverse(body))).status).toBe(200);
  const changed = await worker('events', { ...body, kind: 'POSSIBLE_FALL' });
  expect(changed.status).toBe(409);
  expect(changed.body.code).toBe('EVENT_ID_CONFLICT');
  const equivalent = await worker('events', { ...body, eventId: randomUUID() });
  expect(equivalent.status).toBe(200);
  expect(equivalent.body.incidentId).toBe(receipt.incidentId);
  for (const difference of [
    { kind: 'POSSIBLE_FALL' },
    { runId: randomUUID() },
    { mode: 'LIVE' },
    { signals: { ...body.signals, floorDurationMs: 2001 } },
  ]) {
    const conflict = await worker('events', { ...body, eventId: randomUUID(), ...difference });
    expect(conflict.status).toBe(409);
    expect(conflict.body.code).toBe('EPISODE_CONFLICT');
  }
  expect((await detail(receipt.incidentId)).body).toEqual(before.body);
  expect(await database.eventReceipt.count({ where: { incidentId: receipt.incidentId } })).toBe(2);
  expect(
    await database.notificationIntent.count({ where: { incidentId: receipt.incidentId } }),
  ).toBe(1);
});

test('episódio equivalente concorrente com eventIds distintos continua único', async () => {
  const body = event();
  const responses = await Promise.all(
    Array.from({ length: 10 }, () => worker('events', { ...body, eventId: randomUUID() })),
  );
  expect(responses.filter((response) => response.status === 201)).toHaveLength(1);
  expect(responses.filter((response) => response.status === 200)).toHaveLength(9);
  expect(new Set(responses.map((response) => response.body.incidentId)).size).toBe(1);
  expect(
    await database.eventReceipt.count({ where: { incidentId: responses[0].body.incidentId } }),
  ).toBe(10);
});

test('classes e limites exatos de tempo, TEST e preservação de timestamps originais', async () => {
  for (const [mode, lag, occurredDelta, expected] of [
    ['SIMULATED', 200000, -2000, 'TEST'],
    ['REPLAY', 200000, -2000, 'TEST'],
    ['LIVE', 0, -2000, 'CURRENT'],
    ['LIVE', 120000, -2000, 'CURRENT'],
    ['LIVE', 120001, -2000, 'DELAYED'],
    ['LIVE', -30000, -2000, 'CURRENT'],
    ['LIVE', -30001, -2000, 'CLOCK_UNCERTAIN'],
    ['LIVE', 0, 1, 'CLOCK_UNCERTAIN'],
  ]) {
    const detectedAt = new Date(now.getTime() - lag).toISOString();
    const occurredAt = new Date(Date.parse(detectedAt) + occurredDelta).toISOString();
    const body = event({
      mode,
      sourceOffsetMs: mode === 'REPLAY' ? 2000 : null,
      detectedAt,
      occurredAt,
    });
    const result = await ingest(body);
    expect(result.deliveryClass).toBe(expected);
    expect((await detail(result.incidentId)).body).toMatchObject({
      occurredAt,
      detectedAt,
      mode,
      deliveryClass: expected,
    });
    await executor.drain(200);
    const intent = await database.notificationIntent.findUniqueOrThrow({
      where: { incidentId: result.incidentId },
      include: { delivery: true },
    });
    expect(intent.delivery.urgent).toBe(expected === 'CURRENT');
  }
  const old = event({ detectedAt: new Date(now.getTime() - 30 * 86400000 - 1).toISOString() });
  const future = event({ detectedAt: new Date(now.getTime() + 86400001).toISOString() });
  expect((await worker('events', old)).body.code).toBe('EVENT_TOO_OLD');
  expect((await worker('events', future)).body.code).toBe('INVALID_EVENT_TIME');
  await ingest(event({ detectedAt: new Date(now.getTime() - 30 * 86400000).toISOString() }));
  await ingest(event({ detectedAt: new Date(now.getTime() + 86400000).toISOString() }));
});

test('reenvio depois de 31 dias preserva recibo/classe; tombstone devolve 410', async () => {
  const body = event({ mode: 'LIVE' });
  const original = await ingest(body);
  now = new Date(now.getTime() + 31 * 86400000);
  const repeat = await worker('events', body);
  expect(repeat.status).toBe(200);
  expect(repeat.body).toEqual({ ...original, duplicate: true });
  await database.eventReceipt.update({
    where: { deviceId_eventId: { deviceId: cameraA.device.id, eventId: body.eventId } },
    data: { payload: null, expiredAt: now, incidentId: null },
  });
  const expired = await worker('events', body);
  expect(expired.status).toBe(410);
  expect(expired.body.code).toBe('EVENT_EXPIRED');
  expect(await database.eventReceipt.count({ where: { eventId: body.eventId } })).toBe(1);
});

test('falha na criação da intenção reverte incidente, recibo e auditoria juntos', async () => {
  const body = event();
  await database.$executeRawUnsafe(
    `CREATE FUNCTION test_reject_intent() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'synthetic_transaction_failure'; END $$`,
  );
  await database.$executeRawUnsafe(
    `CREATE TRIGGER test_reject_intent BEFORE INSERT ON "NotificationIntent" FOR EACH ROW EXECUTE FUNCTION test_reject_intent()`,
  );
  const before = await database.auditEntry.count();
  try {
    expect((await worker('events', body)).status).toBeGreaterThanOrEqual(500);
    expect(
      await database.incident.count({ where: { cameraId: cameraA.id, episodeId: body.episodeId } }),
    ).toBe(0);
    expect(await database.eventReceipt.count({ where: { eventId: body.eventId } })).toBe(0);
    expect(await database.auditEntry.count()).toBe(before);
  } finally {
    await database.$executeRawUnsafe('DROP TRIGGER test_reject_intent ON "NotificationIntent"');
    await database.$executeRawUnsafe('DROP FUNCTION test_reject_intent()');
  }
  await ingest(body);
});

test('ações concorrentes idempotentes, versão otimista e resultado original após avanço', async () => {
  const incident = await ingest();
  const body = command('RECOGNIZE');
  const responses = await Promise.all(
    Array.from({ length: 10 }, () => action(incident.incidentId, body)),
  );
  for (const response of responses) {
    expect(response.status).toBe(200);
    expect(response.body).toEqual(responses[0].body);
  }
  expect(responses[0].body.version).toBe(2);
  expect(await database.incidentAction.count({ where: { incidentId: incident.incidentId } })).toBe(
    1,
  );
  const concurrent = await Promise.all([
    action(incident.incidentId, command('START_RESPONSE', 2)),
    action(incident.incidentId, command('ADD_NOTE', 2, { note: 'Anotação sintética' })),
  ]);
  expect(concurrent.map((response) => response.status).sort()).toEqual([200, 409]);
  expect((await action(incident.incidentId, body)).body).toEqual(responses[0].body);
  expect(
    (await action(incident.incidentId, { ...body, action: 'ADD_NOTE', note: 'Diferente' })).body
      .code,
  ).toBe('ACTION_ID_CONFLICT');
  const other = await ingest();
  expect((await action(other.incidentId, body)).body.code).toBe('ACTION_ID_CONFLICT');
  expect(
    await database.auditEntry.count({
      where: { incidentId: incident.incidentId, incidentActionId: { not: null } },
    }),
  ).toBe(2);
});

test('máquina de estados, revisão, desfecho, notas finais e auditoria', async () => {
  const { incidentId } = await ingest();
  expect((await action(incidentId, command('START_RESPONSE'))).body.code).toBe(
    'INVALID_TRANSITION',
  );
  expect(
    (
      await action(
        incidentId,
        command('RESOLVE', 1, { review: 'FALL_REPORTED', outcome: 'ASSISTANCE_RECORDED' }),
      )
    ).status,
  ).toBe(409);
  for (const [name, version, extra, expected] of [
    [
      'SET_REVIEW',
      1,
      { review: 'PERSON_ON_FLOOR_CONFIRMED', note: 'Revisado por pessoa' },
      { status: 'OPEN', review: 'PERSON_ON_FLOOR_CONFIRMED' },
    ],
    ['RECOGNIZE', 2, {}, { status: 'ACKNOWLEDGED' }],
    ['START_RESPONSE', 3, {}, { status: 'IN_PROGRESS' }],
    [
      'RESOLVE',
      4,
      { review: 'FALL_REPORTED', outcome: 'TEST_COMPLETED' },
      { status: 'RESOLVED', review: 'FALL_REPORTED', outcome: 'TEST_COMPLETED' },
    ],
    ['ADD_NOTE', 5, { note: 'Nota após fechamento' }, { status: 'RESOLVED' }],
  ]) {
    const response = await action(incidentId, command(name, version, extra));
    expect(response.status).toBe(200);
    expect(response.body).toMatchObject({ ...expected, version: version + 1 });
  }
  for (const body of [
    command('RECOGNIZE', 6),
    command('DISMISS', 6, { reason: 'TEST_EVENT' }),
    command('SET_REVIEW', 6, { review: 'INCONCLUSIVE' }),
  ])
    expect((await action(incidentId, body)).status).toBe(409);
  const audit = await as(ownerA, 'get', `/v1/audit?incidentId=${incidentId}`);
  expect(audit.status).toBe(200);
  const actions = audit.body.items.filter((entry) => entry.incidentAction);
  expect(actions).toHaveLength(5);
  expect(actions.map((entry) => entry.toVersion).sort()).toEqual([2, 3, 4, 5, 6]);
  expect(
    actions.find((entry) => entry.action === 'INCIDENT_ADD_NOTE').incidentAction.payload.note,
  ).toBe('Nota após fechamento');
  expect((await detail(incidentId)).body).toMatchObject({
    kind: 'PERSON_ON_FLOOR',
    mode: 'SIMULATED',
    deliveryClass: 'TEST',
    status: 'RESOLVED',
    review: 'FALL_REPORTED',
    outcome: 'TEST_COMPLETED',
    version: 6,
  });
});

test('descarte em OPEN, ACKNOWLEDGED e IN_PROGRESS e revisão preservada', async () => {
  for (const state of ['OPEN', 'ACKNOWLEDGED', 'IN_PROGRESS']) {
    const { incidentId } = await ingest();
    let version = 1;
    if (state !== 'OPEN') {
      expect((await action(incidentId, command('RECOGNIZE', version++))).status).toBe(200);
    }
    if (state === 'IN_PROGRESS') {
      expect((await action(incidentId, command('START_RESPONSE', version++))).status).toBe(200);
    }
    const result = await action(
      incidentId,
      command('DISMISS', version, { reason: state === 'OPEN' ? 'FALSE_DETECTION' : 'TEST_EVENT' }),
    );
    expect(result.status).toBe(200);
    expect(result.body).toMatchObject({
      status: 'DISMISSED',
      review: state === 'OPEN' ? 'FALSE_POSITIVE' : 'INCONCLUSIVE',
      outcome: null,
    });
    expect(
      (await action(incidentId, command('ADD_NOTE', version + 1, { note: 'Nota final' }))).status,
    ).toBe(200);
  }
  const { incidentId } = await ingest();
  await action(incidentId, command('SET_REVIEW', 1, { review: 'PERSON_ON_FLOOR_CONFIRMED' }));
  expect(
    (
      await action(
        incidentId,
        command('DISMISS', 2, { reason: 'OTHER', note: 'Observação humana' }),
      )
    ).body.review,
  ).toBe('PERSON_ON_FLOOR_CONFIRMED');
  const acknowledged = await ingest();
  await action(acknowledged.incidentId, command('RECOGNIZE'));
  expect(
    (
      await action(
        acknowledged.incidentId,
        command('RESOLVE', 2, { review: 'INCONCLUSIVE', outcome: 'INCONCLUSIVE' }),
      )
    ).status,
  ).toBe(200);
});

test('falha de auditoria reverte versão e ação sem resultado parcial', async () => {
  const { incidentId } = await ingest();
  const body = command('ADD_NOTE', 1, { note: 'Conteúdo privado não deve aparecer em logs' });
  await database.$executeRawUnsafe(
    `CREATE FUNCTION test_reject_action() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.action='INCIDENT_ADD_NOTE' THEN RAISE EXCEPTION 'synthetic_audit_failure'; END IF; RETURN NEW; END $$`,
  );
  await database.$executeRawUnsafe(
    `CREATE TRIGGER test_reject_action BEFORE INSERT ON "AuditEntry" FOR EACH ROW EXECUTE FUNCTION test_reject_action()`,
  );
  try {
    expect((await action(incidentId, body)).status).toBeGreaterThanOrEqual(500);
    expect((await detail(incidentId)).body.version).toBe(1);
    expect(await database.incidentAction.count({ where: { incidentId } })).toBe(0);
  } finally {
    await database.$executeRawUnsafe('DROP TRIGGER test_reject_action ON "AuditEntry"');
    await database.$executeRawUnsafe('DROP FUNCTION test_reject_action()');
  }
  expect((await action(incidentId, body)).status).toBe(200);
  expect(logs.join('\n')).not.toContain(body.note);
});

test('RBAC, Origin, isolamento de leitura/escrita e separação humano/worker', async () => {
  const { incidentId } = await ingest();
  expect((await detail(incidentId, ownerB)).status).toBe(404);
  expect((await action(incidentId, command('RECOGNIZE'), ownerB)).status).toBe(404);
  expect((await as(ownerB, 'get', `/v1/audit?incidentId=${incidentId}`)).status).toBe(404);
  for (const cameraId of [cameraB.id, otherCamera.id])
    expect((await worker('events', event({ cameraId }))).status).toBe(403);
  expect((await worker('heartbeat', heartbeat({ cameraId: cameraB.id }))).status).toBe(403);
  expect((await as(ownerA, 'post', '/v1/edge/events').send(event())).status).toBe(401);
  expect(
    (
      await api
        .get(`/v1/incidents/${incidentId}`)
        .set('Authorization', `Bearer ${credentialA.token}`)
    ).status,
  ).toBe(401);
  expect(
    (
      await api
        .post(`/v1/incidents/${incidentId}/actions`)
        .set('Cookie', ownerA)
        .send(command('RECOGNIZE'))
    ).status,
  ).toBe(403);
  expect(
    (
      await api
        .post(`/v1/incidents/${incidentId}/actions`)
        .set('Cookie', ownerA)
        .set('Origin', 'https://wrong.invalid')
        .send(command('RECOGNIZE'))
    ).status,
  ).toBe(403);
  expect((await action(incidentId, command('RECOGNIZE'), operatorA)).status).toBe(200);
  expect(
    (await as(operatorA, 'post', `/v1/cameras/${cameraA.id}/device-credentials`).send({})).status,
  ).toBe(403);
  const foreign = await ingest(event({ cameraId: cameraB.id }), credentialB);
  await executor.drain(200);
  for (const path of ['/v1/incidents', '/v1/notifications', '/v1/audit']) {
    const result = await as(ownerA, 'get', path);
    expect(result.status).toBe(200);
    for (const item of result.body.items) expect(item.tenantId).toBe(a.tenantId);
    expect(JSON.stringify(result.body)).not.toContain(foreign.incidentId);
  }
  const disposable = await issue(ownerA, otherCamera.id);
  expect((await as(ownerA, 'delete', `/v1/device-credentials/${disposable.id}`)).status).toBe(204);
  expect((await worker('events', event({ cameraId: otherCamera.id }), disposable)).status).toBe(
    401,
  );
});

test('restrições PostgreSQL recusam relações entre tenants e duplicações', async () => {
  const body = event();
  const { incidentId } = await ingest(body);
  const stored = await database.incident.findUniqueOrThrow({ where: { id: incidentId } });
  const { id: ignoredId, ...incidentData } = stored;
  void ignoredId;
  await expect(
    database.incident.create({
      data: { ...incidentData, id: randomUUID(), episodeId: randomUUID(), siteId: b.siteId },
    }),
  ).rejects.toMatchObject({ code: 'P2003' });
  await expect(
    database.incident.create({
      data: { ...incidentData, id: randomUUID(), episodeId: randomUUID(), cameraId: cameraB.id },
    }),
  ).rejects.toMatchObject({ code: 'P2003' });
  await expect(
    database.incident.create({ data: { ...incidentData, id: randomUUID() } }),
  ).rejects.toMatchObject({ code: 'P2002' });
  await expect(
    database.eventReceipt.create({
      data: {
        tenantId: b.tenantId,
        deviceId: cameraA.device.id,
        eventId: randomUUID(),
        episodeId: randomUUID(),
        payloadHash: '0'.repeat(64),
        receivedAt: now,
        deliveryClass: 'TEST',
      },
    }),
  ).rejects.toMatchObject({ code: 'P2003' });
  await expect(
    database.eventReceipt.create({
      data: {
        tenantId: b.tenantId,
        deviceId: cameraB.device.id,
        incidentId,
        eventId: randomUUID(),
        episodeId: randomUUID(),
        payloadHash: '0'.repeat(64),
        receivedAt: now,
        deliveryClass: 'TEST',
      },
    }),
  ).rejects.toMatchObject({ code: 'P2003' });
  await expect(
    database.notificationIntent.create({
      data: { tenantId: b.tenantId, incidentId, key: randomUUID() },
    }),
  ).rejects.toThrow();
  const intent = await database.notificationIntent.findUniqueOrThrow({ where: { incidentId } });
  await expect(
    database.notificationIntent.update({
      where: { id: intent.id },
      data: { tenantId: b.tenantId },
    }),
  ).rejects.toMatchObject({ code: 'P2003' });
  await expect(
    database.cameraRun.create({
      data: {
        tenantId: b.tenantId,
        cameraId: cameraA.id,
        runId: randomUUID(),
        firstReceivedAt: now,
      },
    }),
  ).rejects.toMatchObject({ code: 'P2003' });
  const receipt = await database.eventReceipt.findUniqueOrThrow({
    where: { deviceId_eventId: { deviceId: cameraA.device.id, eventId: body.eventId } },
  });
  await expect(
    database.eventReceipt.create({ data: { ...receipt, id: randomUUID() } }),
  ).rejects.toMatchObject({ code: 'P2002' });
  await expect(
    database.notificationDelivery.create({
      data: { tenantId: b.tenantId, intentId: intent.id, message: 'SIMULATED', urgent: false },
    }),
  ).rejects.toMatchObject({ code: 'P2003' });
  await expect(
    database.incidentAction.create({
      data: {
        tenantId: a.tenantId,
        incidentId,
        actorId: b.ownerId,
        actionId: randomUUID(),
        action: 'ADD_NOTE',
        payloadHash: '0'.repeat(64),
        result: {},
      },
    }),
  ).rejects.toMatchObject({ code: 'P2003' });
  await expect(
    database.auditEntry.create({
      data: { tenantId: b.tenantId, incidentId, action: 'SYNTHETIC', objectId: incidentId },
    }),
  ).rejects.toMatchObject({ code: 'P2003' });
  await expect(
    database.incidentAction.create({
      data: {
        tenantId: b.tenantId,
        incidentId,
        actorId: b.ownerId,
        actionId: randomUUID(),
        action: 'ADD_NOTE',
        payloadHash: '0'.repeat(64),
        result: {},
      },
    }),
  ).rejects.toMatchObject({ code: 'P2003' });
  const noted = await action(
    incidentId,
    command('ADD_NOTE', 1, { note: 'Teste de FK de auditoria' }),
  );
  expect(noted.status).toBe(200);
  const savedAction = await database.incidentAction.findUniqueOrThrow({
    where: { tenantId_actionId: { tenantId: a.tenantId, actionId: noted.body.actionId } },
  });
  await expect(
    database.incidentAction.create({ data: { ...savedAction, id: randomUUID() } }),
  ).rejects.toMatchObject({ code: 'P2002' });
  await expect(
    database.auditEntry.create({
      data: {
        tenantId: b.tenantId,
        incidentActionId: savedAction.id,
        action: 'SYNTHETIC',
        objectId: incidentId,
      },
    }),
  ).rejects.toMatchObject({ code: 'P2003' });
});

test('filtros, intervalo e cursor estável sem duplicar registros de mesma data', async () => {
  const ids = [];
  for (let index = 0; index < 5; index++)
    ids.push((await ingest(event({ mode: 'REPLAY', sourceOffsetMs: index }))).incidentId);
  let cursor,
    collected = [];
  do {
    const response = await as(
      ownerA,
      'get',
      `/v1/incidents?mode=REPLAY&cameraId=${cameraA.id}&status=OPEN&from=2026-10-21T14:00:00Z&to=2026-10-21T16:00:00Z&limit=2${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`,
    );
    expect(response.status).toBe(200);
    collected.push(...response.body.items.map((item) => item.id));
    cursor = response.body.nextCursor;
  } while (cursor);
  expect(new Set(collected).size).toBe(collected.length);
  expect(collected).toEqual(expect.arrayContaining(ids));
  expect(
    (await as(ownerA, 'get', '/v1/incidents?from=2026-10-22T00:00:00Z&to=2026-10-21T00:00:00Z'))
      .status,
  ).toBe(400);
  expect((await as(ownerA, 'get', '/v1/incidents?mode=UNKNOWN')).status).toBe(400);
});

test('heartbeat: sequência, lease, estados, relógio do servidor e execução aposentada', async () => {
  expect(await health()).toMatchObject({ state: 'OFFLINE', stale: true, receivedAt: null });
  const first = heartbeat({ sentAt: '2000-01-01T00:00:00.000Z' });
  expect((await worker('heartbeat', first)).body.health).toMatchObject({
    state: 'ONLINE',
    stale: false,
    ageMs: 0,
  });
  const receivedAt = (await health()).receivedAt;
  now = new Date(now.getTime() + 15000);
  expect((await worker('heartbeat', { ...first, captureState: 'ERROR' })).body.reason).toBe(
    'OLD_SEQUENCE',
  );
  expect((await health()).receivedAt).toBe(receivedAt);
  expect((await health()).state).toBe('ONLINE');
  const second = heartbeat();
  expect((await worker('heartbeat', second)).body.code).toBe('RUN_CONFLICT');
  now = new Date(now.getTime() + 1);
  expect((await health()).state).toBe('OFFLINE');
  expect((await worker('heartbeat', second)).body.accepted).toBe(true);
  expect((await worker('heartbeat', { ...first, sequence: 100 })).body.reason).toBe('RETIRED_RUN');
  expect(
    (await worker('heartbeat', { ...second, sequence: 1, qualityFlags: ['LOW_LIGHT'] })).body.health
      .state,
  ).toBe('DEGRADED');
  expect(
    (await worker('heartbeat', { ...second, sequence: 2, captureState: 'ERROR', qualityFlags: [] }))
      .body.health.state,
  ).toBe('DEGRADED');
  expect(
    (await worker('heartbeat', { ...second, sequence: 3, captureState: 'PAUSED' })).body.health
      .state,
  ).toBe('PAUSED');
  now = new Date(now.getTime() + 16000);
  expect(await health()).toMatchObject({ state: 'PAUSED', stale: true });
  expect(
    (await worker('heartbeat', { ...second, sequence: 4, captureState: 'ENDED' })).body.health
      .state,
  ).toBe('SOURCE_ENDED');
  now = new Date(now.getTime() + 16000);
  expect(await health()).toMatchObject({ state: 'SOURCE_ENDED', stale: true });
  expect((await worker('heartbeat', { ...second, sequence: 5 })).body.code).toBe('RUN_CLOSED');
  const third = heartbeat({ mode: 'REPLAY' });
  expect((await worker('heartbeat', third)).body.health.heartbeat.mode).toBe('REPLAY');
  const snapshot = await health();
  await ingest(event({ runId: first.runId }));
  expect(await health()).toEqual(snapshot);
  expect((await worker('heartbeat', { ...third, sequence: 1, captureState: 'ENDED' })).status).toBe(
    200,
  );
  expect((await worker('heartbeat', heartbeat())).body.accepted).toBe(true);
});

test('aviso: rollback de entrega/auditoria, retomada após reinício e idempotência', async () => {
  await executor.drain(500);
  const { incidentId } = await ingest();
  const intent = await database.notificationIntent.findUniqueOrThrow({ where: { incidentId } });
  await database.$executeRawUnsafe(
    `CREATE FUNCTION test_reject_notice() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.action='SIMULATED_NOTIFICATION_RECORDED' THEN RAISE EXCEPTION 'synthetic_delivery_failure'; END IF; RETURN NEW; END $$`,
  );
  await database.$executeRawUnsafe(
    `CREATE TRIGGER test_reject_notice BEFORE INSERT ON "AuditEntry" FOR EACH ROW EXECUTE FUNCTION test_reject_notice()`,
  );
  try {
    await expect(executor.drain()).rejects.toThrow();
    expect(await database.notificationDelivery.count({ where: { intentId: intent.id } })).toBe(0);
    expect(
      (await database.notificationIntent.findUniqueOrThrow({ where: { id: intent.id } })).status,
    ).toBe('PENDING');
  } finally {
    await database.$executeRawUnsafe('DROP TRIGGER test_reject_notice ON "AuditEntry"');
    await database.$executeRawUnsafe('DROP FUNCTION test_reject_notice()');
  }
  const restarted = await createApplication(readSettings(), logger, { clock });
  try {
    await restarted.app.init();
    let delivered = false;
    for (let attempt = 0; attempt < 40; attempt++) {
      if (await database.notificationDelivery.count({ where: { intentId: intent.id } })) {
        delivered = true;
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    expect(delivered).toBe(true);
    await Promise.all([executor.drain(), restarted.app.get(NotificationExecutor).drain()]);
  } finally {
    await restarted.app.close();
  }
  await database.notificationIntent.update({
    where: { id: intent.id },
    data: { status: 'PENDING' },
  });
  await executor.drain();
  expect(await database.notificationDelivery.count({ where: { intentId: intent.id } })).toBe(1);
  expect(
    await database.auditEntry.count({
      where: { incidentId, action: 'SIMULATED_NOTIFICATION_RECORDED' },
    }),
  ).toBe(1);
});

test('roteiro PowerShell publicado executa HTTP real sem imprimir segredos', async () => {
  const document = await readFile(
    new URL('../../../docs/VALIDACAO_MANUAL_ETAPA_02.md', import.meta.url),
    'utf8',
  );
  const section = document.split('<!-- smoke:begin -->')[1].split('<!-- smoke:end -->')[0];
  const blocks = [...section.matchAll(/```powershell\r?\n([\s\S]*?)```/g)].map((match) => match[1]);
  expect(blocks).toHaveLength(4);
  const restarted = await createApplication(readSettings(), logger);
  const directory = await mkdtemp(join(tmpdir(), 'radar-http-etapa02-'));
  try {
    await restarted.app.listen(0, '127.0.0.1');
    const port = restarted.app.getHttpServer().address().port;
    const script = join(directory, 'validate.ps1');
    const prelude = `$ErrorActionPreference = 'Stop'\n$radarBase = $env:RADAR_SMOKE_URL\n$radarOrigin = @{ Origin = 'http://127.0.0.1:3000' }\n$radarLogin = @{ email = 'events-owner-a@example.invalid'; password = $env:RADAR_SMOKE_PASSWORD } | ConvertTo-Json -Compress\n$radarIdentity = Invoke-RestMethod "$radarBase/auth/login" -Method Post -Headers $radarOrigin -ContentType 'application/json' -Body $radarLogin -SessionVariable radarSession\n$radarLogin = $null\n`;
    // BOM apenas para o PowerShell 5.1 interpretar corretamente o texto em português.
    await writeFile(script, '\ufeff' + prelude + blocks.join('\n'), 'utf8');
    const result = await new Promise((resolve, reject) => {
      const child = spawn('powershell', ['-NoProfile', '-File', script], {
        cwd: fileURLToPath(new URL('../../../', import.meta.url)),
        env: {
          ...process.env,
          RADAR_SMOKE_PASSWORD: password,
          RADAR_SMOKE_URL: `http://127.0.0.1:${port}/v1`,
        },
        windowsHide: true,
      });
      let output = '';
      child.stdout.on('data', (chunk) => {
        output += chunk;
      });
      child.stderr.on('data', (chunk) => {
        output += chunk;
      });
      child.on('error', reject);
      child.on('exit', (code) => resolve({ code, output }));
    });
    for (const secret of secrets) expect(result.output).not.toContain(secret);
    expect(result).toMatchObject({ code: 0 });
    expect(result.output).toContain('HTTP da etapa 02: ok.');
  } finally {
    await restarted.app.close();
    await rm(directory, { recursive: true, force: true });
  }
});

test('OpenAPI materializa os três schemas e logs/auditoria não expõem credenciais', async () => {
  const response = await api.get('/v1/openapi.json');
  expect(response.status).toBe(200);
  expect(response.body.openapi).toBe('3.1.0');
  expect(Object.keys(response.body.components.schemas)).toEqual(
    expect.arrayContaining(['EventV1', 'HeartbeatV1', 'IncidentActionV1']),
  );
  const storedUsers = await database.user.findMany();
  const credentials = await database.deviceCredential.findMany();
  const recorded = logs.join('\n') + JSON.stringify(await database.auditEntry.findMany());
  for (const secret of [
    ...secrets,
    ...storedUsers.map((user) => user.passwordHash),
    ...credentials.map((item) => item.tokenHash),
  ])
    expect(recorded).not.toContain(secret);
});
