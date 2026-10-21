import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';

// Isolated transport fixture: no demonstration API, database or real credential.
async function simulator(t, handle) {
  const cameraId = randomUUID(),
    token = `synthetic-${randomUUID()}`;
  const requests = [];
  const server = createServer(async (request, response) => {
    let raw = '';
    for await (const chunk of request) raw += chunk;
    const entry = { path: request.url, raw, body: raw ? JSON.parse(raw) : undefined };
    requests.push(entry);
    assert.equal(request.headers.authorization, `Bearer ${token}`);
    const reply = (status, body) => {
      response.writeHead(status, { 'Content-Type': 'application/json' });
      response.end(JSON.stringify(body));
    };
    if (!handle(entry, response, reply, requests)) {
      reply(200, entry.path === '/v1/edge/me' ? { cameraId } : { status: 'ok' });
    }
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(async () => {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  });
  const directory = `.local/etapa03/transport-${randomUUID()}`;
  await mkdir(directory, { recursive: true });
  const config = `${directory}/demo.json`;
  await writeFile(
    config,
    JSON.stringify({
      purpose: 'RADAR_SIMULATED_DEMO',
      apiUrl: `http://127.0.0.1:${server.address().port}/v1`,
      cameraId,
      deviceToken: token,
      durationSeconds: 1,
      resendCount: 10,
    }),
  );
  const child = spawn(
    process.execPath,
    ['scripts/demo/simulate.mjs', '--config', config, '--once'],
    {
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    },
  );
  t.after(() => {
    if (child.exitCode === null) child.kill();
  });
  let output = '';
  for (const stream of [child.stdout, child.stderr])
    stream.on('data', (chunk) => (output += chunk));
  const code = await new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('exit', resolve);
  });
  assert.ok(!output.includes(token), 'Private token must never appear in diagnostics');
  return { code, requests, records: output.trim().split(/\r?\n/).map(JSON.parse) };
}

test(
  'recovers transient failures and lost responses with identical event/heartbeat envelopes',
  { timeout: 20000 },
  async (t) => {
    const events = new Map(),
      heartbeats = new Map();
    let eventRequests = 0;
    const result = await simulator(t, (entry, response, reply) => {
      if (entry.path === '/v1/edge/heartbeat') {
        const key = `${entry.body.runId}:${entry.body.sequence}`;
        if (!heartbeats.has(key)) {
          heartbeats.set(key, entry.raw);
          response.destroy(); // Commit succeeded; its response was lost.
        } else {
          assert.equal(entry.raw, heartbeats.get(key));
          reply(200, { status: 'ok' });
        }
        return true;
      }
      if (entry.path !== '/v1/edge/events') return false;
      eventRequests++;
      if (eventRequests === 1) reply(503, { code: 'DATABASE_UNAVAILABLE' });
      else if (!events.has(entry.body.eventId)) {
        events.set(entry.body.eventId, entry.raw);
        response.destroy();
      } else {
        assert.equal(entry.raw, events.get(entry.body.eventId));
        reply(200, { incidentId: 'synthetic-incident', duplicate: true, deliveryClass: 'TEST' });
      }
      return true;
    });
    assert.equal(result.code, 0);
    assert.equal(events.size, 1);
    assert.equal(heartbeats.size, 2);
    assert.equal(result.records.filter((r) => r.eventId).length, 11);
    assert.ok(result.records.some((r) => r.status === 'retry' && r.code === 'API_UNAVAILABLE'));
    assert.ok(result.records.some((r) => r.status === 'retry' && r.code === 'HTTP_503'));
    assert.equal(result.records.at(-1).captureState, 'ENDED');
  },
);

test(
  'retains the original rejection if the final heartbeat also fails',
  { timeout: 20000 },
  async (t) => {
    const result = await simulator(t, (entry, response, reply) => {
      if (entry.path === '/v1/edge/events') {
        reply(401, { code: 'UNAUTHORIZED' });
        return true;
      }
      if (entry.body?.captureState === 'ENDED') {
        reply(503, { code: 'DATABASE_UNAVAILABLE' });
        return true;
      }
      return false;
    });
    assert.equal(result.code, 1);
    assert.equal(result.requests.filter((r) => r.path === '/v1/edge/events').length, 1);
    const ended = result.requests.filter((r) => r.body?.captureState === 'ENDED');
    assert.equal(ended.length, 4);
    assert.equal(new Set(ended.map((r) => r.raw)).size, 1);
    assert.equal(result.records.at(-1).code, 'HTTP_401');
    assert.ok(result.records.some((r) => r.code === 'ENDED_NOT_CONFIRMED'));
    assert.ok(!result.records.some((r) => r.captureState === 'ENDED'));
  },
);

test('does not retry a forbidden credential or start a run', { timeout: 10000 }, async (t) => {
  const result = await simulator(t, (entry, response, reply) => {
    reply(403, { code: 'FORBIDDEN' });
    return true;
  });
  assert.equal(result.code, 1);
  assert.equal(result.requests.length, 1);
  assert.equal(result.records.at(-1).code, 'HTTP_403');
});

test(
  'stops after four network failures and reports API unavailability',
  { timeout: 15000 },
  async (t) => {
    const result = await simulator(t, (entry, response) => {
      response.destroy();
      return true;
    });
    assert.equal(result.code, 1);
    assert.equal(result.requests.length, 4);
    assert.ok(result.requests.every((r) => r.path === '/v1/edge/me'));
    assert.equal(result.records.at(-1).code, 'API_UNAVAILABLE');
  },
);
