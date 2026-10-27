import 'reflect-metadata';
import { test, expect } from '@jest/globals';
import request from 'supertest';
import { randomBytes, randomUUID } from 'node:crypto';
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
  throw new Error('Execute somente pelo harness PostgreSQL exclusivo.');
}

test('Python LIVE sintético: API fora, restart, ACK perdido, revogação, atraso e erro permanente', async () => {
  const db = createDatabase(dbUrl.href);
  let { app } = await createApplication(readSettings(), false);
  try {
    await app.listen(0, '127.0.0.1');
    const port = app.getHttpServer().address().port;
    const base = `http://127.0.0.1:${port}`;
    const account = await seed(db, {
      tenantSlug: 'resilience-python',
      email: 'resilience@example.invalid',
      password: `Synthetic-${randomBytes(20).toString('hex')}`,
    });
    // All catalog/auth changes belong to this isolated synthetic tenant.
    const worker = await db.camera.create({
      data: {
        tenantId: account.tenantId,
        siteId: account.siteId,
        name: 'Resiliência sintética',
        type: 'WEBCAM',
        device: { create: {} },
      },
    });
    const { tokenHash } = await import('../dist/security.js');
    let token = `dev_${randomBytes(32).toString('base64url')}`;
    const device = await db.device.findFirstOrThrow({ where: { cameraId: worker.id } });
    const issued = await db.deviceCredential.create({
      data: {
        tenantId: account.tenantId,
        deviceId: device.id,
        tokenHash: tokenHash(token),
        version: 1,
      },
    });
    const root = fileURLToPath(new URL('../../../', import.meta.url));
    let deliveryClock = Date.now() / 1000;
    const run = (action, outbox, shift = 0) =>
      new Promise((resolve, reject) => {
        deliveryClock += 1000; // Controlled retry clock; no sleep or production timestamp changes.
        const child = spawn(
          'uv',
          [
            'run',
            '--project',
            'services/edge',
            '--frozen',
            'python',
            'services/edge/tests/resilience_api_probe.py',
            action,
          ],
          {
            cwd: root,
            windowsHide: true,
            env: {
              ...process.env,
              EDGE_API_URL: `${base}/v1`,
              EDGE_DEVICE_TOKEN: token,
              EDGE_TEST_CAMERA: worker.id,
              EDGE_TEST_OUTBOX: outbox,
              EDGE_TIME_SHIFT: String(shift),
              EDGE_TEST_CLOCK: String(deliveryClock),
            },
            stdio: ['ignore', 'pipe', 'pipe'],
          },
        );
        let output = '';
        child.stdout.on('data', (v) => {
          output = (output + v).slice(-8000);
        });
        child.stderr.on('data', () => {});
        child.once('error', () => reject(new Error('Falha ao iniciar probe isolado.')));
        child.once('exit', (code) =>
          code === 0
            ? resolve(JSON.parse(output))
            : reject(new Error(`Probe isolado falhou (exit ${code}); nenhum segredo exibido.`)),
        );
      });
    const path = () => `.local/etapa06/integration/${randomUUID()}/outbox.sqlite`;
    const offline = path();
    await app.close();
    expect((await run('emit', offline)).status).toBe('PENDING');
    ({ app } = await createApplication(readSettings(), false));
    await app.listen(port, '127.0.0.1');
    const restored = await run('deliver', offline);
    expect(restored.status).toBe('DELIVERED');
    expect(restored.confirmation.deliveryClass).toBe('CURRENT');
    expect((await run('deliver', offline)).eventId).toBe(restored.eventId);
    expect(await db.incident.count({ where: { cameraId: worker.id } })).toBe(1);

    const lost = path();
    expect((await run('lost-ack', lost)).status).toBe('PENDING');
    await db.deviceCredential.update({ where: { id: issued.id }, data: { revokedAt: new Date() } });
    expect((await run('deliver', lost)).status).toBe('AUTH_BLOCKED');
    token = `dev_${randomBytes(32).toString('base64url')}`;
    await db.deviceCredential.create({
      data: {
        tenantId: account.tenantId,
        deviceId: device.id,
        tokenHash: tokenHash(token),
        version: 2,
      },
    });
    expect((await run('deliver', lost)).status).toBe('AUTH_BLOCKED');
    const resumed = await run('resume', lost);
    expect(resumed.confirmation.duplicate).toBe(true);
    expect(await db.incident.count({ where: { cameraId: worker.id } })).toBe(2);

    const delayed = await run('emit', path(), -300);
    expect(delayed.confirmation.deliveryClass).toBe('DELAYED');
    const uncertain = await run('emit', path(), 40);
    expect(uncertain.confirmation.deliveryClass).toBe('CLOCK_UNCERTAIN');
    const permanent = path();
    expect((await run('emit', permanent, 172800)).status).toBe('PERMANENT_ERROR');
    expect((await run('deliver', permanent)).attempts).toBe(1);
    const paused = await run('paused-commit', path());
    expect(paused.interruptionInjected).toBe(true);
    expect(paused.preservedPayload).toBe(true);
    expect(paused.confirmation.deliveryClass).toBe('DELAYED');
    const persisted = await db.incident.findUniqueOrThrow({
      where: { id: paused.confirmation.incidentId },
    });
    // Real server wall time is still within 120s; the worker's monotonic
    // interruption proof downgrades delivery without changing the envelope.
    expect(persisted.receivedAt.getTime() - persisted.detectedAt.getTime()).toBeLessThan(120000);
    await app.get(NotificationExecutor).drain();
    for (const result of [delayed, uncertain, paused]) {
      const notices = await db.notificationDelivery.findMany({
        where: { intent: { incidentId: result.confirmation.incidentId } },
      });
      expect(notices).toHaveLength(1);
      expect(notices[0].urgent).toBe(false);
    }
    const hb = {
      schemaVersion: 1,
      cameraId: worker.id,
      runId: randomUUID(),
      mode: 'LIVE',
      sequence: 1,
      sentAt: new Date().toISOString(),
      captureState: 'RUNNING',
      qualityFlags: [],
      analysisFps: 5,
      outboxPending: 0,
      lastFrameAgeMs: 0,
      inferenceState: 'ONE_VALID_POSE',
      versions: {
        worker: 'synthetic-live',
        model: 'fixture',
        policy: 'floor-v0.1',
        calibration: 'fixture',
      },
    };
    const api = request(app.getHttpServer());
    const post = (value) =>
      api.post('/v1/edge/heartbeat').set('Authorization', `Bearer ${token}`).send(value);
    expect((await post(hb)).body.accepted).toBe(true);
    expect((await post({ ...hb, runId: randomUUID() })).status).toBe(409);
    expect((await post({ ...hb, sequence: 2, captureState: 'PAUSED' })).body.health.state).toBe(
      'PAUSED',
    );
    expect((await post({ ...hb, sequence: 3, captureState: 'ENDED' })).body.health.state).toBe(
      'SOURCE_ENDED',
    );
  } finally {
    await app.close();
    await db.$disconnect();
  }
}, 120000);
