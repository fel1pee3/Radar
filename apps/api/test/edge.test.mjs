import 'reflect-metadata';
import { test, expect } from '@jest/globals';
import request from 'supertest';
import { randomBytes } from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createApplication } from '../dist/application.js';
import { readSettings } from '../dist/config.js';
import { createDatabase } from '../dist/database.js';
import { seed } from '../dist/bootstrap.js';
import { NotificationExecutor } from '../dist/notifications.js';

const dbUrl = new URL(process.env.DATABASE_URL ?? '');
if (
  !/^radar-test-[a-f0-9]{12}$/.test(process.env.RADAR_TEST_CONTAINER ?? '') ||
  dbUrl.hostname !== '127.0.0.1' ||
  ['5432', '15432', ''].includes(dbUrl.port) ||
  !/^\/radar_test_[a-f0-9]{12}$/.test(dbUrl.pathname)
) {
  throw new Error('Execute via pnpm.cmd test:api em banco exclusivo.');
}

test('Python real: features → episódio/outbox → timeout após commit → restart → ACK duplicado', async () => {
  const database = createDatabase(dbUrl.href);
  const { app } = await createApplication(readSettings(), false);
  try {
    await app.listen(0, '127.0.0.1');
    const api = request(app.getHttpServer());
    const password = `Synthetic-${randomBytes(20).toString('hex')}`;
    const account = await seed(database, {
      tenantSlug: 'edge-python',
      email: 'edge-python@example.invalid',
      password,
    });
    const login = await api
      .post('/v1/auth/login')
      .set('Origin', 'http://127.0.0.1:3000')
      .send({ email: 'edge-python@example.invalid', password });
    expect(login.status).toBe(200);
    const cookie = login.headers['set-cookie'][0].split(';')[0];
    const asOwner = (method, path) =>
      api[method](path).set('Cookie', cookie).set('Origin', 'http://127.0.0.1:3000');
    const camera = await asOwner('post', '/v1/cameras').send({
      siteId: account.siteId,
      name: 'Python sintético',
      type: 'FILE',
    });
    expect(camera.status).toBe(201);
    const credential = await asOwner(
      'post',
      `/v1/cameras/${camera.body.id}/device-credentials`,
    ).send({});
    expect(credential.status).toBe(201);
    const root = fileURLToPath(new URL('../../../', import.meta.url));
    const url = await app.getUrl();
    const result = await new Promise((resolve, reject) => {
      const child = spawn(
        'uv',
        [
          'run',
          '--project',
          'services/edge',
          '--frozen',
          'python',
          'services/edge/tests/edge_api_probe.py',
        ],
        {
          cwd: root,
          windowsHide: true,
          env: {
            ...process.env,
            EDGE_API_URL: `${url}/v1`,
            EDGE_DEVICE_TOKEN: credential.body.token,
            EDGE_TEST_CAMERA: camera.body.id,
          },
          stdio: ['ignore', 'pipe', 'pipe'],
        },
      );
      let output = '';
      child.stdout.on('data', (data) => {
        output = (output + data).slice(-4000);
      });
      child.stderr.on('data', () => {});
      child.once('error', () => reject(new Error('Não foi possível iniciar uv.')));
      child.once('exit', (code) =>
        code === 0
          ? resolve(JSON.parse(output))
          : reject(new Error(`Probe Python falhou: exit ${code}; nenhum segredo exibido.`)),
      );
    });
    expect(result.duplicateAck).toBe(true);
    const detail = await asOwner('get', `/v1/incidents/${result.incidentId}`);
    expect(detail.status).toBe(200);
    expect(detail.body.mode).toBe('REPLAY');
    expect(detail.body.deliveryClass).toBe('TEST');
    expect(detail.body.versions.worker).toBe('edge-temporal-v1');
    expect(detail.body.signals.floorDurationMs).toBe(2000);
    expect(detail.body.pose.length).toBeGreaterThan(0);
    expect(await database.incident.count({ where: { cameraId: camera.body.id } })).toBe(1);
    expect(await database.eventReceipt.count({ where: { eventId: result.eventId } })).toBe(1);
    await app.get(NotificationExecutor).drain();
    const delivery = await database.notificationDelivery.findMany({
      where: { intent: { incidentId: result.incidentId } },
    });
    expect(delivery).toHaveLength(1);
    expect(delivery.every((item) => !item.urgent)).toBe(true);
  } finally {
    await app.close();
    await database.$disconnect();
  }
}, 60000);
