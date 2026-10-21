import { readFile, realpath } from 'node:fs/promises';
import { resolve, relative } from 'node:path';
import { randomUUID } from 'node:crypto';
import { createInterface } from 'node:readline';
import { setTimeout as pause } from 'node:timers/promises';
import { validateContract } from '../../packages/contracts/dist/index.js';

export function syntheticPose() {
  return [
    [11, 0.28, 0.53],
    [12, 0.29, 0.66],
    [13, 0.2, 0.5],
    [14, 0.2, 0.7],
    [15, 0.13, 0.53],
    [16, 0.13, 0.73],
    [23, 0.5, 0.55],
    [24, 0.5, 0.67],
    [25, 0.68, 0.57],
    [26, 0.69, 0.7],
    [27, 0.86, 0.58],
    [28, 0.86, 0.72],
    [29, 0.89, 0.59],
    [30, 0.89, 0.73],
    [31, 0.93, 0.57],
    [32, 0.93, 0.71],
  ].map(([index, x, y]) => ({ index, x, y, visibility: 1 }));
}
const output = (value) => console.log(JSON.stringify(value));
async function main() {
  const args = process.argv.slice(2);
  const position = args.indexOf('--config');
  if (args.some((arg, index) => arg !== '--once' && arg !== '--config' && index !== position + 1))
    throw new Error('INVALID_ARGUMENT');
  const filename = await realpath(
    resolve(position >= 0 ? (args[position + 1] ?? '') : '.local/demo.json'),
  );
  const directory = await realpath(resolve('.local'));
  const location = relative(directory, filename);
  if (location.startsWith('..') || resolve(directory, location) !== filename)
    throw new Error('PRIVATE_CONFIG_REQUIRED');
  const config = JSON.parse((await readFile(filename, 'utf8')).replace(/^\uFEFF/, ''));
  const url = new URL(config.apiUrl);
  if (
    config.purpose !== 'RADAR_SIMULATED_DEMO' ||
    url.protocol !== 'http:' ||
    url.hostname !== '127.0.0.1' ||
    url.pathname !== '/v1' ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    typeof config.deviceToken !== 'string' ||
    !config.deviceToken ||
    !Number.isInteger(config.durationSeconds) ||
    config.durationSeconds < 1 ||
    config.durationSeconds > 600 ||
    !Number.isInteger(config.resendCount) ||
    config.resendCount < 0 ||
    config.resendCount > 100
  )
    throw new Error('INVALID_DEMO_CONFIG');
  async function http(path, body) {
    // Preserve the exact envelope when a response is lost after the API commits it.
    const payload = body ? JSON.stringify(body) : undefined;
    for (let attempt = 1; attempt <= 4; attempt++) {
      try {
        const response = await fetch(`${url.href}${path}`, {
          method: body ? 'POST' : 'GET',
          headers: {
            Authorization: `Bearer ${config.deviceToken}`,
            ...(body ? { 'Content-Type': 'application/json' } : {}),
          },
          body: payload,
          signal: AbortSignal.timeout(5000),
        });
        if (!response.ok) {
          await response.body?.cancel();
          throw new Error(`HTTP_${response.status}`);
        }
        return { status: response.status, body: await response.json() };
      } catch (error) {
        const network =
          error instanceof TypeError || ['TimeoutError', 'AbortError'].includes(error?.name);
        const transient = network || /^HTTP_(502|503|504)$/.test(error?.message);
        const code = network ? 'API_UNAVAILABLE' : error?.message;
        if (!transient || attempt === 4) throw new Error(code);
        output({ status: 'retry', code, operation: path, attempt: attempt + 1, maxAttempts: 4 });
        await pause(500 * 2 ** (attempt - 1));
      }
    }
  }
  const identity = await http('/edge/me');
  if (identity.body.cameraId !== config.cameraId) throw new Error('CAMERA_SCOPE_MISMATCH');
  const sample = JSON.parse(
    await readFile(
      new URL('../../packages/contracts/fixtures/event-simulated.json', import.meta.url),
      'utf8',
    ),
  );
  const runId = randomUUID();
  const time = Date.now();
  const event = {
    ...sample,
    eventId: randomUUID(),
    episodeId: randomUUID(),
    runId,
    cameraId: config.cameraId,
    mode: 'SIMULATED',
    occurredAt: new Date(time - 2000).toISOString(),
    detectedAt: new Date(time).toISOString(),
    pose: syntheticPose(),
  };
  if (!validateContract('event-v1', event)) throw new Error('INVALID_EVENT');
  let sequence = 0,
    stopping = false,
    requested = 0,
    started = false;
  const stop = () => {
    stopping = true;
  };
  process.on('SIGINT', stop);
  process.on('SIGTERM', stop);
  const input = process.stdin.isTTY
    ? createInterface({ input: process.stdin, output: process.stdout })
    : null;
  input?.on('line', (line) => {
    if (line.trim().toLowerCase() === 'r') requested++;
    if (line.trim().toLowerCase() === 'q') stop();
  });
  input?.on('SIGINT', stop);
  async function heartbeat(captureState) {
    const body = {
      schemaVersion: 1,
      cameraId: config.cameraId,
      runId,
      mode: 'SIMULATED',
      sequence: sequence++,
      sentAt: new Date().toISOString(),
      captureState,
      qualityFlags: [],
      analysisFps: 0,
      outboxPending: 0,
      lastFrameAgeMs: null,
      inferenceState: 'WARMING_UP',
      versions: event.versions,
    };
    if (!validateContract('heartbeat-v1', body)) throw new Error('INVALID_HEARTBEAT');
    await http('/edge/heartbeat', body);
  }
  async function send() {
    const response = await http('/edge/events', event);
    output({
      mode: 'SIMULATED',
      eventId: event.eventId,
      ...response.body,
      status: response.status,
    });
  }
  let failure;
  try {
    await heartbeat('RUNNING');
    started = true;
    await send();
    for (let index = 0; index < config.resendCount && !stopping; index++) await send();
    output({
      mode: 'SIMULATED',
      runId,
      message:
        'Evento artificial com pose sintética. Digite r e Enter para reenviar; q e Enter ou Ctrl+C para encerrar.',
    });
    let lastHeartbeat = Date.now();
    while (
      !args.includes('--once') &&
      !stopping &&
      Date.now() - time < config.durationSeconds * 1000
    ) {
      if (Date.now() - lastHeartbeat >= 5000) {
        await heartbeat('RUNNING');
        lastHeartbeat = Date.now();
      }
      if (requested > 0) {
        requested--;
        await send();
      }
      await pause(250);
    }
  } catch (error) {
    failure = error;
  } finally {
    input?.close();
    process.removeListener('SIGINT', stop);
    process.removeListener('SIGTERM', stop);
    if (started) {
      try {
        await heartbeat('ENDED');
        output({ mode: 'SIMULATED', runId, captureState: 'ENDED' });
      } catch (error) {
        output({ status: 'error', code: 'ENDED_NOT_CONFIRMED', mode: 'SIMULATED', runId });
        failure ??= error;
      }
    }
  }
  if (failure) throw failure;
}
main().catch((error) => {
  console.error(
    JSON.stringify({
      status: 'error',
      code: /^(HTTP_\d{3}|INVALID_[A-Z_]+|PRIVATE_CONFIG_REQUIRED|CAMERA_SCOPE_MISMATCH|API_UNAVAILABLE)$/.test(
        error?.message,
      )
        ? error.message
        : 'DEMO_UNAVAILABLE',
      message:
        error?.message === 'API_UNAVAILABLE'
          ? 'A API local não respondeu após quatro tentativas. Confira o terminal de dev:api. Um evento já aceito permanece no painel.'
          : 'Confira API, credencial da câmera exclusiva e configuração privada em .local. Nenhum segredo foi exibido.',
    }),
  );
  process.exitCode = 1;
});
