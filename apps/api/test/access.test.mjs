import 'reflect-metadata';
import { beforeAll, afterAll, test, expect } from '@jest/globals';
import request from 'supertest';
import { randomBytes, randomUUID } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { createApplication } from '../dist/application.js';
import { createDatabase } from '../dist/database.js';
import { readSettings } from '../dist/config.js';
import { seed, createOperator } from '../dist/bootstrap.js';
import { checkPassword, tokenHash } from '../dist/security.js';

const url = new URL(process.env.DATABASE_URL ?? '');
const container = process.env.RADAR_TEST_CONTAINER;
if (
  url.hostname !== '127.0.0.1' ||
  ['5432', '15432', ''].includes(url.port) ||
  !/^\/radar_test_[a-f0-9]{12}$/.test(url.pathname) ||
  !/^radar-test-[a-f0-9]{12}$/.test(container ?? '')
) {
  throw new Error('Suite exige o container e o banco exclusivos criados por pnpm.cmd test:api.');
}
const origin = 'http://127.0.0.1:3000';
const secrets = new Set([url.password, url.href]);
secrets.add('rtsp://private:synthetic@camera.invalid');
secrets.add('synthetic-camera-password');
const password = `Synthetic-${randomBytes(18).toString('hex')}`;
secrets.add(password);
const logs = [];
const logger = Object.fromEntries(
  ['log', 'error', 'warn', 'debug', 'verbose', 'fatal'].map((level) => [
    level,
    (...args) => logs.push(JSON.stringify({ level, args })),
  ]),
);
const database = createDatabase(url.href);
let app, api, ownerA, ownerB, operatorA, a, b, cameraA, cameraB, credentialA, credentialB;

async function login(email, secret = password) {
  const response = await api
    .post('/v1/auth/login')
    .set('Origin', origin)
    .send({ email, password: secret });
  expect(response.status).toBe(200);
  const cookie = response.headers['set-cookie'][0].split(';')[0];
  secrets.add(cookie.split('=')[1]);
  return { cookie, response };
}
function as(cookie, method, path) {
  return api[method](path).set('Cookie', cookie).set('Origin', origin);
}
async function issue(cookie, cameraId) {
  const response = await as(cookie, 'post', `/v1/cameras/${cameraId}/device-credentials`).send({});
  expect(response.status).toBe(201);
  secrets.add(response.body.token);
  return response.body;
}
function control(action) {
  const result = spawnSync('docker', [action, container], { encoding: 'utf8' });
  if (result.status !== 0) throw new Error('Falha ao controlar somente o container de testes.');
}

beforeAll(async () => {
  expect(await database.user.count()).toBe(0);
  expect(await database.tenant.count()).toBe(0);
  const built = await createApplication(readSettings(), logger);
  app = built.app;
  await app.listen(0, '127.0.0.1');
  api = request(app.getHttpServer());
  a = await seed(database, { tenantSlug: 'test-a', email: 'owner-a@example.invalid', password });
  b = await seed(database, { tenantSlug: 'test-b', email: 'owner-b@example.invalid', password });
  await createOperator(database, {
    tenantSlug: 'test-a',
    email: 'operator-a@example.invalid',
    password,
  });
  ownerA = (await login('owner-a@example.invalid')).cookie;
  ownerB = (await login('owner-b@example.invalid')).cookie;
  operatorA = (await login('operator-a@example.invalid')).cookie;
  for (const [cookie, fixture] of [
    [ownerA, a],
    [ownerB, b],
  ]) {
    const response = await as(cookie, 'post', '/v1/cameras').send({
      siteId: fixture.siteId,
      name: 'Câmera sintética',
      type: 'WEBCAM',
    });
    expect(response.status).toBe(201);
    if (fixture === a) cameraA = response.body;
    else cameraB = response.body;
  }
});

afterAll(async () => {
  try {
    if (app) await app.close();
  } finally {
    await database.$disconnect();
  }
});

test('migração real em banco vazio cria tabelas, índices e registro de migração', async () => {
  const migrations =
    await database.$queryRaw`SELECT migration_name, finished_at FROM "_prisma_migrations"`;
  expect(migrations).toHaveLength(1);
  expect(migrations[0].migration_name).toBe('20261021000100_initial_access');
  expect(migrations[0].finished_at).not.toBeNull();
  const tables =
    await database.$queryRaw`SELECT tablename FROM pg_tables WHERE schemaname='public'`;
  expect(tables.map((row) => row.tablename)).toEqual(
    expect.arrayContaining([
      'Tenant',
      'User',
      'Session',
      'Site',
      'Camera',
      'Device',
      'DeviceCredential',
      'AuditEntry',
    ]),
  );
});

test('seed repetido preserva senha, registros editados e IDs; colisão não cria outro tenant', async () => {
  const before = await database.user.findUniqueOrThrow({ where: { id: a.ownerId } });
  await database.site.update({
    where: { id: a.siteId },
    data: { name: 'Nome editado preservado' },
  });
  const result = await seed(database, {
    tenantSlug: 'test-a',
    email: 'OWNER-A@EXAMPLE.INVALID',
    password: 'Another-synthetic-password',
  });
  expect(result).toEqual({ ...a, created: false });
  const after = await database.user.findUniqueOrThrow({ where: { id: a.ownerId } });
  expect(after.passwordHash).toBe(before.passwordHash);
  expect(after.passwordHash.startsWith('$argon2id$')).toBe(true);
  expect(await checkPassword(after.passwordHash, password)).toBe(true);
  expect(await database.site.findUnique({ where: { id: a.siteId } })).toMatchObject({
    name: 'Nome editado preservado',
  });
  expect(await database.user.count()).toBe(3);
  await expect(
    seed(database, { tenantSlug: 'must-rollback', email: before.email, password }),
  ).rejects.toThrow();
  expect(await database.tenant.count()).toBe(2);
  await expect(
    seed(database, { tenantSlug: 'test-a', email: 'changed-owner@example.invalid', password }),
  ).rejects.toThrow();
  expect(await database.user.count()).toBe(3);
  const existingOperator = await createOperator(database, {
    tenantSlug: 'test-a',
    email: 'operator-a@example.invalid',
    password: 'Another-operator-password',
  });
  expect(existingOperator.created).toBe(false);
  expect(await database.user.count()).toBe(3);
});

test('login válido usa cookie HttpOnly/Lax/Path=/ e sessão hasheada de oito horas', async () => {
  const { cookie, response } = await login('owner-a@example.invalid');
  expect(response.headers['set-cookie'][0]).toContain('HttpOnly');
  expect(response.headers['set-cookie'][0]).toContain('SameSite=Lax');
  expect(response.headers['set-cookie'][0]).toContain('Path=/');
  expect(response.headers['set-cookie'][0]).not.toContain('Secure');
  const token = cookie.split('=')[1];
  const session = await database.session.findUniqueOrThrow({
    where: { tokenHash: tokenHash(token) },
  });
  expect(session.tokenHash).not.toBe(token);
  const duration = session.expiresAt.getTime() - session.createdAt.getTime();
  expect(duration).toBeGreaterThan(28790000);
  expect(duration).toBeLessThanOrEqual(28801000);
  expect(JSON.stringify(response.body)).not.toContain(token);
  expect(response.body.passwordHash).toBeUndefined();
  expect((await as(cookie, 'get', '/v1/auth/me')).body).toMatchObject({
    role: 'OWNER',
    tenantId: a.tenantId,
  });
});

test('login inválido e usuário desconhecido retornam a mesma mensagem; corpo limitado', async () => {
  const wrong = await api
    .post('/v1/auth/login')
    .set('Origin', origin)
    .send({ email: 'owner-a@example.invalid', password: 'wrong-synthetic-secret' });
  const absent = await api
    .post('/v1/auth/login')
    .set('Origin', origin)
    .send({ email: 'absent@example.invalid', password: 'wrong-synthetic-secret' });
  secrets.add('wrong-synthetic-secret');
  expect(wrong.status).toBe(401);
  expect(absent.status).toBe(401);
  expect(wrong.body).toEqual(absent.body);
  expect(
    (await api.post('/v1/auth/login').set('Origin', origin).send({ email: 'invalid', password }))
      .status,
  ).toBe(400);
  expect(
    (
      await api
        .post('/v1/auth/login')
        .set('Origin', origin)
        .send({ padding: 'x'.repeat(70000) })
    ).status,
  ).toBe(413);
});

test('logout revoga sessão e limpa cookie; sessão expirada ou usuário inativo não autentica', async () => {
  const first = await login('owner-a@example.invalid');
  const response = await as(first.cookie, 'post', '/v1/auth/logout').send({});
  expect(response.status).toBe(204);
  expect(response.headers['set-cookie'][0]).toContain('Expires=Thu, 01 Jan 1970');
  expect((await as(first.cookie, 'get', '/v1/auth/me')).status).toBe(401);
  const second = await login('owner-a@example.invalid');
  await database.session.update({
    where: { tokenHash: tokenHash(second.cookie.split('=')[1]) },
    data: { expiresAt: new Date(Date.now() - 1) },
  });
  expect((await as(second.cookie, 'get', '/v1/auth/me')).status).toBe(401);
  await database.user.update({ where: { id: a.ownerId }, data: { active: false } });
  try {
    expect((await as(ownerA, 'get', '/v1/sites')).status).toBe(401);
  } finally {
    await database.user.update({ where: { id: a.ownerId }, data: { active: true } });
  }
});

test('Origin externo ou ausente é rejeitado em login e mutações por cookie, inclusive logout', async () => {
  for (const value of [
    null,
    'https://evil.example',
    'http://localhost:3000',
    `${origin}.evil.example`,
  ]) {
    for (const path of ['/v1/auth/login', '/v1/sites', '/v1/auth/logout']) {
      let operation = api.post(path).set('Cookie', ownerA);
      if (value) operation = operation.set('Origin', value);
      const response = await operation.send(
        path.endsWith('login')
          ? { email: 'owner-a@example.invalid', password }
          : { name: 'CSRF', timezone: 'UTC' },
      );
      expect(response.status).toBe(403);
    }
  }
  expect((await as(ownerA, 'get', '/v1/auth/me')).status).toBe(200);
});

test('OPERATOR lê locais/câmeras mas não configura, emite, rotaciona ou revoga', async () => {
  expect((await as(operatorA, 'get', '/v1/sites')).status).toBe(200);
  expect((await as(operatorA, 'get', '/v1/cameras')).status).toBe(200);
  for (const [method, path, body] of [
    ['post', '/v1/sites', { name: 'Proibido', timezone: 'UTC' }],
    ['patch', `/v1/sites/${a.siteId}`, { name: 'Proibido' }],
    ['post', '/v1/cameras', { name: 'Proibido', siteId: a.siteId, type: 'FILE' }],
    ['patch', `/v1/cameras/${cameraA.id}`, { name: 'Proibido' }],
    ['post', `/v1/cameras/${cameraA.id}/device-credentials`, {}],
    ['delete', `/v1/device-credentials/${randomUUID()}`, {}],
  ])
    expect((await as(operatorA, method, path).send(body)).status).toBe(403);
});

test('OWNER cria/altera; payloads privados, tenantId e campos desconhecidos são rejeitados', async () => {
  const response = await as(ownerA, 'post', '/v1/sites').send({
    name: 'Outro local',
    timezone: 'UTC',
  });
  expect(response.status).toBe(201);
  expect(
    (await as(ownerA, 'patch', `/v1/sites/${response.body.id}`).send({ name: 'Local atualizado' }))
      .status,
  ).toBe(200);
  const changed = await as(ownerA, 'patch', `/v1/cameras/${cameraA.id}`).send({
    name: 'Câmera atualizada',
    expectedRunning: true,
    siteId: response.body.id,
  });
  expect(changed.status).toBe(200);
  expect(changed.body.device.id).toBe(cameraA.device.id);
  for (const extra of [
    { tenantId: b.tenantId },
    { rtspUri: 'rtsp://private:synthetic@camera.invalid' },
    { password: 'synthetic-camera-password' },
  ]) {
    expect(
      (
        await as(ownerA, 'post', '/v1/cameras').send({
          name: 'Privada',
          type: 'RTSP',
          siteId: a.siteId,
          ...extra,
        })
      ).status,
    ).toBe(400);
  }
  expect(
    (await as(ownerA, 'post', '/v1/sites').send({ name: 'Inválido', timezone: 'Timezone/Invalid' }))
      .status,
  ).toBe(400);
  expect((await as(ownerA, 'get', '/v1/cameras?tenantId=forged')).status).toBe(400);
});

test('isolamento HTTP entre tenants em leituras, alterações, referências e credenciais', async () => {
  const sites = await as(ownerA, 'get', '/v1/sites');
  const cameras = await as(ownerA, 'get', '/v1/cameras');
  expect(sites.body.items.every((site) => site.tenantId === a.tenantId)).toBe(true);
  expect(cameras.body.items.every((camera) => camera.tenantId === a.tenantId)).toBe(true);
  for (const cookie of [ownerA, operatorA]) {
    expect((await as(cookie, 'get', `/v1/sites/${b.siteId}`)).status).toBe(404);
    expect((await as(cookie, 'get', `/v1/cameras/${cameraB.id}`)).status).toBe(404);
  }
  expect((await as(ownerA, 'patch', `/v1/sites/${b.siteId}`).send({ name: 'Cross' })).status).toBe(
    404,
  );
  expect(
    (await as(ownerA, 'patch', `/v1/cameras/${cameraB.id}`).send({ name: 'Cross' })).status,
  ).toBe(404);
  expect(
    (
      await as(ownerA, 'post', '/v1/cameras').send({
        name: 'Cross',
        type: 'WEBCAM',
        siteId: b.siteId,
      })
    ).status,
  ).toBe(404);
  expect(
    (await as(ownerA, 'patch', `/v1/cameras/${cameraA.id}`).send({ siteId: b.siteId })).status,
  ).toBe(404);
  expect(
    (await as(ownerA, 'post', `/v1/cameras/${cameraB.id}/device-credentials`).send({})).status,
  ).toBe(404);
});

test('chaves compostas bloqueiam referências cruzadas diretamente no PostgreSQL', async () => {
  const standalone = await database.camera.create({
    data: { tenantId: b.tenantId, siteId: b.siteId, name: 'Fixture FK', type: 'FILE' },
  });
  const invalid = [
    () =>
      database.camera.create({
        data: { tenantId: a.tenantId, siteId: b.siteId, name: 'Cross', type: 'FILE' },
      }),
    () =>
      database.session.create({
        data: {
          tenantId: a.tenantId,
          userId: b.ownerId,
          tokenHash: tokenHash(randomUUID()),
          expiresAt: new Date(),
        },
      }),
    () => database.device.create({ data: { tenantId: a.tenantId, cameraId: standalone.id } }),
    () =>
      database.deviceCredential.create({
        data: {
          tenantId: a.tenantId,
          deviceId: cameraB.device.id,
          tokenHash: tokenHash(randomUUID()),
          version: 99,
        },
      }),
    () =>
      database.auditEntry.create({
        data: { tenantId: a.tenantId, actorId: b.ownerId, action: 'INVALID_FIXTURE' },
      }),
  ];
  for (const operation of invalid)
    await expect(operation()).rejects.toMatchObject({ code: 'P2003' });
});

test('paginação estável não duplica registros nem aceita cursores/limites inválidos', async () => {
  for (let index = 0; index < 3; index++)
    expect(
      (await as(ownerA, 'post', '/v1/sites').send({ name: `Página ${index}`, timezone: 'UTC' }))
        .status,
    ).toBe(201);
  const ids = [];
  let cursor;
  do {
    const response = await as(
      ownerA,
      'get',
      `/v1/sites?limit=2${cursor ? `&cursor=${cursor}` : ''}`,
    );
    expect(response.status).toBe(200);
    ids.push(...response.body.items.map((item) => item.id));
    cursor = response.body.nextCursor;
  } while (cursor);
  expect(new Set(ids).size).toBe(ids.length);
  expect(ids).toHaveLength(await database.site.count({ where: { tenantId: a.tenantId } }));
  for (const query of ['limit=0', 'limit=101', 'limit=bad', 'cursor=invalid'])
    expect((await as(ownerA, 'get', `/v1/sites?${query}`)).status).toBe(400);
});

test('worker tem token hasheado, escopo de câmera e identidade estável após rotação', async () => {
  credentialA = await issue(ownerA, cameraA.id);
  credentialB = await issue(ownerB, cameraB.id);
  const stored = await database.deviceCredential.findUniqueOrThrow({
    where: { id: credentialA.id },
  });
  expect(stored.tokenHash).toBe(tokenHash(credentialA.token));
  expect(stored.tokenHash).not.toBe(credentialA.token);
  const first = await api.get('/v1/edge/me').set('Authorization', `Bearer ${credentialA.token}`);
  expect(first.status).toBe(200);
  expect(first.body).toMatchObject({
    deviceId: cameraA.device.id,
    cameraId: cameraA.id,
    tenantId: a.tenantId,
  });
  expect(first.body.token).toBeUndefined();
  expect(first.body.tokenHash).toBeUndefined();
  const rotated = await issue(ownerA, cameraA.id);
  expect(rotated.deviceId).toBe(credentialA.deviceId);
  expect(rotated.version).toBe(2);
  expect(
    (await api.get('/v1/edge/me').set('Authorization', `Bearer ${credentialA.token}`)).status,
  ).toBe(401);
  credentialA = rotated;
  expect(
    (await api.get('/v1/edge/me').set('Authorization', `Bearer ${rotated.token}`)).status,
  ).toBe(200);
  expect((await as(ownerA, 'delete', `/v1/device-credentials/${credentialB.id}`)).status).toBe(404);
  expect((await as(operatorA, 'delete', `/v1/device-credentials/${rotated.id}`)).status).toBe(403);
});

test('emissões concorrentes deixam uma única credencial ativa e revogação é efetiva', async () => {
  const issued = await Promise.all([issue(ownerA, cameraA.id), issue(ownerA, cameraA.id)]);
  expect(issued[0].deviceId).toBe(issued[1].deviceId);
  expect(new Set(issued.map((value) => value.version)).size).toBe(2);
  const current = issued.find(
    (value) => value.version === Math.max(...issued.map((item) => item.version)),
  );
  expect(
    await database.deviceCredential.count({
      where: { deviceId: current.deviceId, revokedAt: null },
    }),
  ).toBe(1);
  for (const value of issued)
    expect(
      (await api.get('/v1/edge/me').set('Authorization', `Bearer ${value.token}`)).status,
    ).toBe(value === current ? 200 : 401);
  expect((await as(ownerA, 'delete', `/v1/device-credentials/${current.id}`)).status).toBe(204);
  expect((await as(ownerA, 'delete', `/v1/device-credentials/${current.id}`)).status).toBe(204);
  expect(
    (await api.get('/v1/edge/me').set('Authorization', `Bearer ${current.token}`)).status,
  ).toBe(401);
  expect((await api.get('/v1/edge/me').set('Authorization', 'Bearer dev_invalid')).status).toBe(
    401,
  );
  expect((await api.get('/v1/device-credentials/' + current.id).set('Cookie', ownerA)).status).toBe(
    404,
  );
});

test('sessão humana e bearer não se substituem, nem com sessão e header misturados', async () => {
  expect((await api.get('/v1/edge/me').set('Cookie', ownerA)).status).toBe(401);
  expect(
    (await api.get('/v1/edge/me').set('Authorization', `Bearer ${ownerA.split('=')[1]}`)).status,
  ).toBe(401);
  expect(
    (await api.get('/v1/sites').set('Authorization', `Bearer ${credentialB.token}`)).status,
  ).toBe(401);
  expect(
    (await as(ownerA, 'get', '/v1/sites').set('Authorization', `Bearer ${credentialB.token}`))
      .status,
  ).toBe(401);
});

test('limitação de login devolve 429 após dez tentativas da conta', async () => {
  for (let index = 0; index < 10; index++)
    expect(
      (
        await api
          .post('/v1/auth/login')
          .set('Origin', origin)
          .send({ email: 'rate@example.invalid', password: 'wrong-synthetic-secret' })
      ).status,
    ).toBe(401);
  expect(
    (
      await api
        .post('/v1/auth/login')
        .set('Origin', origin)
        .send({ email: 'rate@example.invalid', password: 'wrong-synthetic-secret' })
    ).status,
  ).toBe(429);
});

test('HTTP inseguro é recusado fora do desenvolvimento; cookie Secure em HTTPS', async () => {
  expect(() => readSettings({ ...process.env, NODE_ENV: 'production' })).toThrow();
  expect(() => readSettings({ ...process.env, API_HOST: '0.0.0.0' })).toThrow();
  const secure = readSettings({
    ...process.env,
    NODE_ENV: 'production',
    WEB_ORIGIN: 'https://127.0.0.1:3000',
    ALLOW_INSECURE_LOCAL_HTTP: 'false',
  });
  const built = await createApplication(secure, logger);
  try {
    await built.app.listen(0, '127.0.0.1');
    const response = await request(built.app.getHttpServer())
      .post('/v1/auth/login')
      .set('Origin', secure.webOrigin)
      .send({ email: 'owner-b@example.invalid', password });
    expect(response.status).toBe(200);
    expect(response.headers['set-cookie'][0]).toContain('Secure');
    secrets.add(response.headers['set-cookie'][0].split(';')[0].split('=')[1]);
  } finally {
    await built.app.close();
  }
});

test('readiness consulta banco real, retorna 503 no desligamento e recupera; liveness continua 200', async () => {
  expect((await api.get('/v1/health/ready')).status).toBe(200);
  control('stop');
  try {
    expect((await api.get('/v1/health/live')).body).toEqual({ status: 'ok' });
    expect((await api.get('/v1/health/ready')).status).toBe(503);
    expect((await as(ownerA, 'get', '/v1/sites')).status).toBe(503);
  } finally {
    control('start');
  }
  let restored = false;
  for (let attempt = 0; attempt < 20; attempt++) {
    if ((await api.get('/v1/health/ready')).status === 200) {
      restored = true;
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  expect(restored).toBe(true);
});

test('CLI de seed/operador usa configuração privada e preserva contas ao repetir', async () => {
  const environment = {
    ...process.env,
    BOOTSTRAP_TENANT_SLUG: 'test-cli',
    BOOTSTRAP_EMAIL: 'cli-owner@example.invalid',
    BOOTSTRAP_PASSWORD: password,
    OPERATOR_EMAIL: 'cli-operator@example.invalid',
    OPERATOR_PASSWORD: password,
  };
  function execute(command) {
    const response = spawnSync(process.execPath, ['dist/cli.js', command], {
      env: environment,
      encoding: 'utf8',
    });
    expect(response.status).toBe(0);
    const output = response.stdout + response.stderr;
    for (const secret of secrets) expect(output.includes(secret)).toBe(false);
    return JSON.parse(response.stdout.trim());
  }
  const first = execute('seed');
  expect(first.created).toBe(true);
  environment.BOOTSTRAP_PASSWORD = 'Changed-private-cli-password';
  const second = execute('seed');
  expect(second.ownerId).toBe(first.ownerId);
  expect(second.created).toBe(false);
  const saved = await database.user.findUniqueOrThrow({ where: { id: first.ownerId } });
  expect(await checkPassword(saved.passwordHash, password)).toBe(true);
  expect(execute('operator').created).toBe(true);
  expect(execute('operator').created).toBe(false);
});

test('OpenAPI deriva dos endpoints/DTOs; logs e auditoria não contêm segredos', async () => {
  const response = await api.get('/v1/openapi.json');
  expect(response.status).toBe(200);
  expect(Object.keys(response.body.paths)).toEqual(
    expect.arrayContaining([
      '/v1/auth/login',
      '/v1/sites',
      '/v1/cameras',
      '/v1/health/ready',
      '/v1/edge/me',
    ]),
  );
  const audit = await database.auditEntry.findMany();
  expect(audit.map((entry) => entry.action)).toEqual(
    expect.arrayContaining([
      'LOGIN_SUCCEEDED',
      'LOGIN_FAILED',
      'LOGOUT',
      'CAMERA_CREATED',
      'DEVICE_CREDENTIAL_ISSUED',
      'DEVICE_CREDENTIAL_REVOKED',
    ]),
  );
  const storedUsers = await database.user.findMany();
  const storedCredentials = await database.deviceCredential.findMany();
  const recorded = logs.join('\n') + JSON.stringify(audit);
  for (const secret of [
    ...secrets,
    ...storedUsers.map((user) => user.passwordHash),
    ...storedCredentials.map((item) => item.tokenHash),
  ])
    expect(recorded.includes(secret)).toBe(false);
});
