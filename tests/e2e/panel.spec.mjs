import { test as base, expect } from '@playwright/test';
import { randomUUID } from 'node:crypto';
import { spawn, spawnSync } from 'node:child_process';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { createDatabase } from '../../apps/api/dist/database.js';
import { seed, createOperator } from '../../apps/api/dist/bootstrap.js';

const url = new URL(process.env.DATABASE_URL ?? '');
if (
  url.hostname !== '127.0.0.1' ||
  ['5432', '15432', ''].includes(url.port) ||
  !/^\/radar_e2e_[a-f0-9]{12}$/.test(url.pathname) ||
  !/^radar-e2e-[a-f0-9]{12}$/.test(process.env.RADAR_E2E_CONTAINER ?? '')
)
  throw new Error('Recursos E2E exclusivos obrigatórios.');
const origin = process.env.RADAR_E2E_WEB_URL,
  apiUrl = process.env.RADAR_E2E_API_URL,
  password = process.env.RADAR_E2E_PASSWORD;
const test = base.extend({
  fixture: async ({ request }, use) => {
    const database = createDatabase(url.href);
    const key = randomUUID();
    const email = `owner-${key}@example.invalid`,
      operatorEmail = `operator-${key}@example.invalid`;
    const tenant = await seed(database, { tenantSlug: `e2e-${key}`, email, password });
    await createOperator(database, { tenantSlug: `e2e-${key}`, email: operatorEmail, password });
    const login = await request.post(`${apiUrl}/auth/login`, {
      headers: { Origin: origin },
      data: { email, password },
    });
    expect(login.status()).toBe(200);
    const cookie = login.headers()['set-cookie'].split(';')[0];
    const headers = { Origin: origin, Cookie: cookie };
    const cameraResponse = await request.post(`${apiUrl}/cameras`, {
      headers,
      data: { siteId: tenant.siteId, name: `Fonte ${key.slice(0, 6)}`, type: 'FILE' },
    });
    expect(cameraResponse.status()).toBe(201);
    const camera = await cameraResponse.json();
    const tokenResponse = await request.post(`${apiUrl}/cameras/${camera.id}/device-credentials`, {
      headers,
      data: {},
    });
    expect(tokenResponse.status()).toBe(201);
    const credential = await tokenResponse.json();
    const sample = JSON.parse(
      await readFile('packages/contracts/fixtures/event-simulated.json', 'utf8'),
    );
    async function publish(overrides = {}) {
      const event = {
        ...sample,
        eventId: randomUUID(),
        episodeId: randomUUID(),
        runId: randomUUID(),
        cameraId: camera.id,
        occurredAt: new Date(Date.now() - 2000).toISOString(),
        detectedAt: new Date().toISOString(),
        ...overrides,
      };
      const response = await request.post(`${apiUrl}/edge/events`, {
        headers: { Authorization: `Bearer ${credential.token}` },
        data: event,
      });
      expect(response.status()).toBe(201);
      return { event, ...(await response.json()) };
    }
    try {
      await use({
        ...tenant,
        email,
        operatorEmail,
        password,
        database,
        camera,
        credential,
        headers,
        publish,
      });
    } finally {
      await database.$disconnect();
    }
  },
});
async function login(page, fixture, operator = false) {
  await page.goto('/login');
  await page
    .getByLabel('E-mail', { exact: true })
    .fill(operator ? fixture.operatorEmail : fixture.email);
  await page.getByLabel('Senha', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Visão geral', exact: true })).toBeVisible();
}
async function submit(page, action) {
  await page.getByRole('combobox', { name: 'Ação', exact: true }).selectOption(action);
  await page.getByRole('button', { name: 'Registrar ação', exact: true }).click();
  await expect(page.getByText('Ação registrada com sucesso.', { exact: true })).toBeVisible();
}

test('pose RTMO experimental mantém score distinto de visibilidade no painel', async ({
  page,
  fixture,
}) => {
  const cases = JSON.parse(await readFile('packages/contracts/fixtures/cases.json', 'utf8'));
  const value = cases.find((item) => item.name === 'event-rtmo-score').value;
  const receipt = await fixture.publish({
    mode: 'REPLAY',
    sourceOffsetMs: 2000,
    pose: value.pose,
    versions: value.versions,
  });
  await login(page, fixture);
  await page.goto(`/incidentes/${receipt.incidentId}`);
  await expect(page.getByRole('img', { name: 'Esqueleto corporal de evidência' })).toBeVisible();
  await expect(page.locator('figcaption')).toContainText('RTMO experimental');
  await expect(page.locator('figcaption')).toContainText('não comprova visibilidade');
  await expect(page.locator('figcaption')).not.toContainText('Pontos com visibilidade');
  await expect(page.locator('.pose-figure svg circle')).toHaveCount(value.pose.length);
});

test('login, proteção de rota, cookie HttpOnly, logout e ausência de cache de outra conta', async ({
  page,
  context,
  request,
  fixture,
}) => {
  await page.goto('/incidentes');
  await expect(page.getByRole('button', { name: 'Entrar', exact: true })).toBeVisible();
  await expect(page.locator('.incident-list')).toHaveCount(0);
  await login(page, fixture);
  const cookies = await context.cookies();
  expect(cookies.find((cookie) => cookie.name === 'radar_session')?.httpOnly).toBe(true);
  expect(await page.evaluate(() => localStorage.length)).toBe(0);
  expect(
    (await request.get(`${origin}/api/auth/me`, { headers: fixture.headers })).headers()[
      'cache-control'
    ],
  ).toBe('no-store');
  const csrf = await request.post(`${origin}/api/sites`, {
    headers: { Cookie: fixture.headers.Cookie },
    data: { name: 'CSRF', timezone: 'UTC' },
  });
  expect(csrf.status()).toBe(403);
  await page.getByRole('button', { name: 'Sair da conta' }).click();
  await expect(page.getByRole('button', { name: 'Entrar', exact: true })).toBeVisible();
  await page.goBack();
  await expect(page.locator('.incident-list')).toHaveCount(0);
  await login(page, fixture, true);
  await expect(
    page.getByRole('navigation').getByRole('link', { name: 'Configuração' }),
  ).toHaveCount(0);
});

test('simulador real → incidente com pose → revisão e desfecho persistidos → aviso único', async ({
  page,
  fixture,
}, info) => {
  await login(page, fixture);
  await page.getByRole('link', { name: 'Fontes', exact: true }).click();
  const card = page.locator('.source-card').filter({ hasText: fixture.camera.name });
  await expect(card.getByText('Sem heartbeat.', { exact: false })).toBeVisible();
  await expect(card.getByText('Execução ativa', { exact: true })).toHaveCount(0);
  const directory = `.local/etapa03/demo-${randomUUID()}`;
  await mkdir(directory, { recursive: true });
  const config = `${directory}/demo.json`;
  await writeFile(
    config,
    '\ufeff' +
      JSON.stringify({
        purpose: 'RADAR_SIMULATED_DEMO',
        apiUrl,
        cameraId: fixture.camera.id,
        deviceToken: fixture.credential.token,
        durationSeconds: 7,
        resendCount: 10,
      }),
  );
  let output = '';
  const child = spawn(
    process.execPath,
    [process.env.npm_execpath, 'demo:simulate', '--config', config],
    { env: process.env, windowsHide: true },
  );
  child.stdout.on('data', (chunk) => {
    output += chunk;
  });
  child.stderr.on('data', (chunk) => {
    output += chunk;
  });
  const done = new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('exit', (code) => resolve(code));
  });
  try {
    await expect(card.getByText('Heartbeat do simulador;', { exact: false })).toBeVisible();
    await page.getByRole('link', { name: 'Incidentes', exact: true }).click();
    await expect(
      page.locator('.incident-row').filter({ hasText: fixture.camera.name }),
    ).toHaveCount(1);
    await page.locator('.incident-row').filter({ hasText: fixture.camera.name }).click();
    await expect(
      page.getByRole('img', { name: 'Esqueleto de pose sintética simulada' }),
    ).toBeVisible();
    await expect(page.getByText('Duração no piso (ms)', { exact: true })).toBeVisible();
    await expect(page.locator('figcaption')).toContainText('POSE SINTÉTICA · EVIDÊNCIA SIMULADA');
    expect(await done).toBe(0);
    expect(output).not.toContain(fixture.credential.token);
    expect(output).not.toContain(password);
    const records = output
      .split(/\r?\n/)
      .filter((line) => line.startsWith('{'))
      .map((line) => JSON.parse(line));
    const events = records.filter((record) => record.eventId);
    expect(events).toHaveLength(11);
    expect(events.filter((record) => record.status === 201)).toHaveLength(1);
    expect(events.filter((record) => record.status === 200)).toHaveLength(10);
    const incidentId = events[0].incidentId;
    const storedCamera = await fixture.database.camera.findUniqueOrThrow({
      where: { id: fixture.camera.id },
    });
    expect(storedCamera.lastHeartbeat.captureState).toBe('ENDED');
    expect(Number(storedCamera.heartbeatSequence)).toBeGreaterThanOrEqual(2);
    await submit(page, 'RECOGNIZE');
    await expect(page.getByText('Versão exibida: 2.', { exact: false })).toBeVisible();
    await page.getByRole('combobox', { name: 'Ação', exact: true }).selectOption('SET_REVIEW');
    await page
      .getByRole('combobox', { name: 'Revisão humana', exact: true })
      .selectOption('PERSON_ON_FLOOR_CONFIRMED');
    await page
      .getByLabel('Nota', { exact: true })
      .fill('Revisão sintética registrada pelo navegador.');
    await page.getByRole('button', { name: 'Registrar ação', exact: true }).click();
    await expect(page.getByText('Versão exibida: 3.', { exact: false })).toBeVisible();
    await submit(page, 'START_RESPONSE');
    await expect(page.getByText('Versão exibida: 4.', { exact: false })).toBeVisible();
    await page.getByRole('combobox', { name: 'Ação', exact: true }).selectOption('RESOLVE');
    await page
      .getByRole('combobox', { name: 'Revisão humana', exact: true })
      .selectOption('PERSON_ON_FLOOR_CONFIRMED');
    await page
      .getByRole('combobox', { name: 'Desfecho', exact: true })
      .selectOption('TEST_COMPLETED');
    await page.getByRole('button', { name: 'Registrar ação', exact: true }).click();
    await expect(page.getByText('Versão exibida: 5.', { exact: false })).toBeVisible();
    await page.reload();
    await expect(
      page.locator('.detail-summary').getByText('Encerrado', { exact: true }),
    ).toBeVisible();
    await expect(
      page
        .locator('.timeline')
        .getByText('Revisão sintética registrada pelo navegador.', { exact: true }),
    ).toBeVisible();
    expect(
      (await fixture.database.incident.findUniqueOrThrow({ where: { id: incidentId } })).outcome,
    ).toBe('TEST_COMPLETED');
    expect(await fixture.database.eventReceipt.count({ where: { incidentId } })).toBe(1);
    expect(await fixture.database.notificationIntent.count({ where: { incidentId } })).toBe(1);
    await page.screenshot({ path: info.outputPath('detalhe.png'), fullPage: true });
    await page.screenshot({ path: info.outputPath('detalhe-viewport.png') });
    await page.getByRole('link', { name: 'Avisos locais', exact: true }).click();
    await expect(page.locator(`a[href="/incidentes/${incidentId}"]`)).toHaveCount(1);
    await expect(page.getByText('Canal SIMULATED', { exact: true })).toBeVisible();
    expect(
      await fixture.database.notificationDelivery.count({ where: { intent: { incidentId } } }),
    ).toBe(1);
  } finally {
    if (child.exitCode === null) child.kill();
  }
});

test('OWNER configura local/câmera e emite token uma vez; metadados permitem revogação após recarga', async ({
  page,
  request,
  fixture,
}) => {
  await login(page, fixture);
  await page.getByRole('link', { name: 'Configuração', exact: true }).click();
  await page.getByLabel('Nome do local', { exact: true }).fill('Local do navegador');
  await page.getByRole('button', { name: 'Criar local', exact: true }).click();
  await expect(page.getByText('Cadastro criado.', { exact: true })).toBeVisible();
  await page.getByLabel('Nome da câmera', { exact: true }).fill('Demo exclusiva UI');
  await page
    .getByRole('combobox', { name: 'Local', exact: true })
    .selectOption({ label: 'Local do navegador' });
  await page.getByRole('button', { name: 'Criar câmera', exact: true }).click();
  const editor = page.locator('.camera-editor').filter({ hasText: 'Demo exclusiva UI' });
  await expect(editor).toBeVisible();
  await editor.getByRole('button', { name: 'Editar câmera', exact: true }).click();
  await editor.getByLabel('Nome', { exact: true }).fill('Demo exclusiva UI editada');
  await editor.getByRole('button', { name: 'Salvar câmera', exact: true }).click();
  await expect(
    editor.getByRole('heading', { name: 'Demo exclusiva UI editada', exact: true }),
  ).toBeVisible();
  await editor.getByRole('button', { name: 'Emitir/rotacionar credencial', exact: true }).click();
  await editor.getByRole('button', { name: 'Confirmar emissão/rotação', exact: true }).click();
  const secret = await editor.getByTestId('issued-token').textContent();
  expect(secret).toBeTruthy();
  expect(await page.evaluate(() => localStorage.length)).toBe(0);
  await editor.getByRole('button', { name: 'Ocultei e guardei o token', exact: true }).click();
  await page.reload();
  await expect(page.getByTestId('issued-token')).toHaveCount(0);
  const camera = await fixture.database.camera.findFirstOrThrow({
    where: { tenantId: fixture.tenantId, name: 'Demo exclusiva UI editada' },
  });
  const credentials = await request.get(`${apiUrl}/cameras/${camera.id}/device-credentials`, {
    headers: fixture.headers,
  });
  expect(credentials.status()).toBe(200);
  const data = await credentials.json();
  expect(Object.keys(data.items[0]).sort()).toEqual([
    'createdAt',
    'deviceId',
    'id',
    'revokedAt',
    'version',
  ]);
  expect(data.items).toHaveLength(1);
  await page
    .locator('.camera-editor')
    .filter({ hasText: 'Demo exclusiva UI editada' })
    .getByRole('button', { name: 'Revogar credencial', exact: true })
    .click();
  await expect(page.getByText('Credencial revogada.', { exact: true })).toBeVisible();
  expect(
    (
      await request.get(`${apiUrl}/edge/me`, { headers: { Authorization: `Bearer ${secret}` } })
    ).status(),
  ).toBe(401);
});

test('OPERATOR revisa, não configura nem lê metadados de credenciais; outro tenant é isolado', async ({
  page,
  request,
  fixture,
}) => {
  const incident = await fixture.publish();
  await login(page, fixture, true);
  await page.goto(`/incidentes/${incident.incidentId}`);
  await expect(
    page.getByRole('heading', { name: 'Possível pessoa no chão', exact: true }),
  ).toBeVisible();
  await submit(page, 'RECOGNIZE');
  await page.goto('/configuracao');
  await expect(page.getByRole('heading', { name: 'Configuração restrita' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Criar câmera', exact: true })).toHaveCount(0);
  const operator = await request.post(`${apiUrl}/auth/login`, {
    headers: { Origin: origin },
    data: { email: fixture.operatorEmail, password },
  });
  const cookie = operator.headers()['set-cookie'].split(';')[0];
  expect(
    (
      await request.get(`${apiUrl}/cameras/${fixture.camera.id}/device-credentials`, {
        headers: { Cookie: cookie },
      })
    ).status(),
  ).toBe(403);
  const other = await seed(fixture.database, {
    tenantSlug: `other-${randomUUID()}`,
    email: `other-${randomUUID()}@example.invalid`,
    password,
  });
  const otherLogin = await request.post(`${apiUrl}/auth/login`, {
    headers: { Origin: origin },
    data: {
      email: (
        await fixture.database.user.findUniqueOrThrow({
          where: { id: other.ownerId },
          select: { email: true },
        })
      ).email,
      password,
    },
  });
  const otherCookie = otherLogin.headers()['set-cookie'].split(';')[0];
  expect(
    (
      await request.get(`${apiUrl}/cameras/${fixture.camera.id}/device-credentials`, {
        headers: { Cookie: otherCookie },
      })
    ).status(),
  ).toBe(404);
  expect(
    (
      await request.get(`${apiUrl}/incidents/${incident.incidentId}`, {
        headers: { Cookie: otherCookie },
      })
    ).status(),
  ).toBe(404);
});

test('conflito real mantém nota e exige nova intenção; perda de confirmação reutiliza actionId', async ({
  page,
  request,
  fixture,
}) => {
  const incident = await fixture.publish();
  await login(page, fixture);
  await page.goto(`/incidentes/${incident.incidentId}`);
  await page.getByLabel('Nota', { exact: true }).fill('Rascunho preservado durante conflito.');
  await page.route(
    `**/api/incidents/${incident.incidentId}/actions`,
    async (route) => {
      const body = route.request().postDataJSON();
      const concurrent = await request.post(`${apiUrl}/incidents/${incident.incidentId}/actions`, {
        headers: fixture.headers,
        data: {
          actionId: randomUUID(),
          expectedVersion: body.expectedVersion,
          action: 'RECOGNIZE',
        },
      });
      expect(concurrent.status()).toBe(200);
      await route.continue();
    },
    { times: 1 },
  );
  await page.getByRole('button', { name: 'Registrar ação', exact: true }).click();
  await expect(page.getByText('Conflito de versão ou intenção.', { exact: false })).toBeVisible();
  await expect(page.getByLabel('Nota', { exact: true })).toHaveValue(
    'Rascunho preservado durante conflito.',
  );
  expect(
    await fixture.database.incidentAction.count({ where: { incidentId: incident.incidentId } }),
  ).toBe(1);
  await page
    .getByRole('button', { name: 'Conferi o estado; preparar nova tentativa', exact: true })
    .click();
  expect(
    await fixture.database.incidentAction.count({ where: { incidentId: incident.incidentId } }),
  ).toBe(1);
  let original;
  await page.route(
    `**/api/incidents/${incident.incidentId}/actions`,
    async (route) => {
      original = route.request().postDataJSON();
      const response = await route.fetch();
      expect(response.status()).toBe(200);
      await route.abort('failed');
    },
    { times: 1 },
  );
  await page.getByRole('button', { name: 'Registrar ação', exact: true }).click();
  await expect(
    page.getByRole('button', { name: 'Reenviar mesma tentativa', exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Reenviar mesma tentativa', exact: true }).click();
  await expect(page.getByText('Ação registrada com sucesso.', { exact: true })).toBeVisible();
  expect(
    await fixture.database.incidentAction.count({ where: { incidentId: incident.incidentId } }),
  ).toBe(2);
  expect(
    await fixture.database.incidentAction.count({
      where: { tenantId: fixture.tenantId, actionId: original.actionId },
    }),
  ).toBe(1);
});

test('API indisponível preserva dados e rascunho; expiração pede login sem perder texto', async ({
  page,
  fixture,
}) => {
  const incident = await fixture.publish();
  await login(page, fixture);
  await page.goto(`/incidentes/${incident.incidentId}`);
  await page.getByLabel('Nota', { exact: true }).fill('Texto que não pode desaparecer.');
  const container = process.env.RADAR_E2E_CONTAINER;
  try {
    expect(spawnSync('docker', ['stop', container], { encoding: 'utf8' }).status).toBe(0);
    await expect(page.getByText('Atualização indisponível.', { exact: true }).first()).toBeVisible({
      timeout: 20000,
    });
    await expect(
      page.getByRole('heading', { name: 'Possível pessoa no chão', exact: true }),
    ).toBeVisible();
    await expect(page.getByLabel('Nota', { exact: true })).toHaveValue(
      'Texto que não pode desaparecer.',
    );
    await expect(page.getByRole('button', { name: 'Registrar ação', exact: true })).toBeDisabled();
  } finally {
    expect(spawnSync('docker', ['start', container], { encoding: 'utf8' }).status).toBe(0);
  }
  await expect
    .poll(
      async () => {
        try {
          return (await fetch(`${apiUrl}/health/ready`)).status;
        } catch {
          return 0;
        }
      },
      { timeout: 20000 },
    )
    .toBe(200);
  await expect(page.getByRole('button', { name: 'Registrar ação', exact: true })).toBeEnabled({
    timeout: 20000,
  });
  await fixture.database.session.updateMany({
    where: { tenantId: fixture.tenantId },
    data: { expiresAt: new Date(Date.now() - 1000) },
  });
  await expect(
    page.getByRole('heading', { name: 'Sua sessão expirou', exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel('Nota', { exact: true })).not.toBeVisible();
  await page.getByLabel('E-mail', { exact: true }).fill(fixture.email);
  await page.getByLabel('Senha', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await expect(page.getByLabel('Nota', { exact: true })).toHaveValue(
    'Texto que não pode desaparecer.',
  );
});

test('falha de consulta não mantém fonte aparentemente saudável', async ({
  page,
  request,
  fixture,
}) => {
  const cases = JSON.parse(await readFile('packages/contracts/fixtures/cases.json', 'utf8'));
  const heartbeat = {
    ...cases.find((item) => item.name === 'heartbeat-v1-basic').value,
    cameraId: fixture.camera.id,
    runId: randomUUID(),
    sentAt: new Date().toISOString(),
  };
  expect(
    (
      await request.post(`${apiUrl}/edge/heartbeat`, {
        headers: { Authorization: `Bearer ${fixture.credential.token}` },
        data: heartbeat,
      })
    ).status(),
  ).toBe(200);
  await login(page, fixture);
  await page.getByRole('link', { name: 'Fontes', exact: true }).click();
  const card = page.locator('.source-card').filter({ hasText: fixture.camera.name });
  await expect(card.getByText('Execução ativa', { exact: true })).toBeVisible();
  try {
    expect(
      spawnSync('docker', ['stop', process.env.RADAR_E2E_CONTAINER], { encoding: 'utf8' }).status,
    ).toBe(0);
    await expect(card.getByText('Estado não atualizado', { exact: true })).toBeVisible({
      timeout: 20000,
    });
    await expect(card.getByText('Execução ativa', { exact: true })).toHaveCount(0);
    await expect(
      card.getByText('API indisponível. Último estado conhecido:', { exact: false }),
    ).toBeVisible();
  } finally {
    expect(
      spawnSync('docker', ['start', process.env.RADAR_E2E_CONTAINER], { encoding: 'utf8' }).status,
    ).toBe(0);
  }
  await expect
    .poll(
      async () => {
        try {
          return (await fetch(`${apiUrl}/health/ready`)).status;
        } catch {
          return 0;
        }
      },
      { timeout: 20000 },
    )
    .toBe(200);
});

test('polling pausa/retoma sem sobreposição; filtros, paginação e layout permanecem utilizáveis', async ({
  page,
  fixture,
}, info) => {
  for (let index = 0; index < 21; index++) await fixture.publish();
  await login(page, fixture);
  await page.goto(`/incidentes?mode=SIMULATED&cameraId=${fixture.camera.id}`);
  await expect(page.locator('.incident-row')).toHaveCount(20);
  let count = 0;
  page.on('request', (req) => {
    if (req.url().includes('/api/incidents?')) count++;
  });
  await page.evaluate(() => {
    Object.defineProperty(document, 'hidden', { configurable: true, value: true });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await page.waitForTimeout(2500);
  const paused = count;
  await page.waitForTimeout(2500);
  expect(count).toBe(paused);
  await page.evaluate(() => {
    Object.defineProperty(document, 'hidden', { configurable: true, value: false });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await expect.poll(() => count).toBeGreaterThan(paused);
  let active = 0,
    maximum = 0,
    completed = 0;
  await page.route(
    '**/api/incidents?*',
    async (route) => {
      active++;
      maximum = Math.max(maximum, active);
      try {
        const response = await route.fetch();
        await new Promise((resolve) => setTimeout(resolve, 3000));
        await route.fulfill({ response });
        completed++;
      } finally {
        active--;
      }
    },
    { times: 2 },
  );
  await expect.poll(() => completed, { timeout: 15000 }).toBe(2);
  expect(maximum).toBe(1);
  const firstIds = await page
    .locator('.incident-row')
    .evaluateAll((rows) => rows.map((row) => row.getAttribute('href')));
  await page.getByRole('link', { name: 'Próxima página →', exact: true }).click();
  await expect(page.locator('.incident-row')).toHaveCount(1);
  expect(firstIds).not.toContain(await page.locator('.incident-row').getAttribute('href'));
  await page.getByRole('link', { name: 'Primeira página', exact: true }).click();
  await expect(page.locator('.incident-row')).toHaveCount(20);
  await expect(page.getByRole('combobox', { name: 'Modo', exact: true })).toHaveValue('SIMULATED');
  await expect(page.getByRole('combobox', { name: 'Câmera', exact: true })).toHaveValue(
    fixture.camera.id,
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  await page.screenshot({ path: info.outputPath('lista.png'), fullPage: true });
  await page.getByRole('link', { name: 'Visão geral', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Visão geral', exact: true })).toBeVisible();
  await expect(page.locator('.incident-row')).toHaveCount(6);
  await expect(page.locator('.source-card')).toHaveCount(1);
  await page.screenshot({ path: info.outputPath('visao-geral.png'), fullPage: true });
});

test('evidência JPEG sintética: leitura, falha transitória, permissões e exclusão auditada', async ({
  page,
  request,
  fixture,
}) => {
  const { syntheticJpeg } = await import('../../apps/api/test/synthetic-jpeg.mjs');
  const pref = await request.patch(`${apiUrl}/cameras/${fixture.camera.id}/evidence-preference`, {
    headers: fixture.headers,
    data: { mode: 'snapshot', authorized: true },
  });
  expect(pref.status()).toBe(200);
  const published = await fixture.publish({ evidenceMode: 'snapshot' });
  await login(page, fixture);
  await page.goto(`/incidentes/${published.incidentId}`);
  await expect(
    page.getByText('Imagem ausente ou aguardando envio do worker.', { exact: true }),
  ).toBeVisible();
  const uploaded = await request.post(`${apiUrl}/edge/events/${published.eventId}/snapshot`, {
    headers: { Authorization: `Bearer ${fixture.credential.token}`, 'Content-Type': 'image/jpeg' },
    data: await syntheticJpeg(),
  });
  expect(uploaded.status()).toBe(201);
  await expect(page.getByText('Imagem disponível.', { exact: true })).toBeVisible();
  await page.route(`**/api/incidents/${published.incidentId}/snapshot`, (route) =>
    route.fulfill({ status: 503, body: '{}' }),
  );
  await page.getByRole('button', { name: 'Abrir imagem', exact: true }).click();
  await expect(page.getByText(/Leitura temporariamente indisponível/)).toBeVisible();
  await page.unroute(`**/api/incidents/${published.incidentId}/snapshot`);
  await page.getByRole('button', { name: 'Abrir imagem', exact: true }).click();
  await expect(page.getByAltText('Evidência pontual do evento')).toBeVisible();
  await mkdir('.local/etapa07/screenshots', { recursive: true });
  await page.screenshot({
    path: `.local/etapa07/screenshots/${test.info().project.name}-snapshot.png`,
    fullPage: true,
  });
  // A controlled short client deadline also revokes a loaded blob if polling is offline.
  await page.route(`**/api/incidents/${published.incidentId}`, async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    await route.fulfill({
      response,
      json: {
        ...data,
        snapshot: { ...data.snapshot, expiresAt: new Date(Date.now() + 2500).toISOString() },
      },
    });
  });
  await page.reload();
  await page.getByRole('button', { name: 'Abrir imagem', exact: true }).click();
  await expect(page.getByAltText('Evidência pontual do evento')).toBeVisible();
  await page.route('**/api/incidents/*', (route) => route.abort());
  await expect(page.getByText('Imagem expirada.', { exact: true })).toBeVisible({ timeout: 6000 });
  await expect(page.getByAltText('Evidência pontual do evento')).toHaveCount(0);
  await page.unrouteAll({ behavior: 'wait' });
  await page.getByRole('button', { name: 'Sair da conta' }).click();
  await login(page, fixture, true);
  await page.goto(`/incidentes/${published.incidentId}`);
  await expect(page.getByRole('button', { name: 'Abrir imagem', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Excluir imagem', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Sair da conta' }).click();
  await login(page, fixture);
  await page.goto(`/incidentes/${published.incidentId}`);
  await page.getByRole('button', { name: 'Excluir imagem', exact: true }).click();
  await expect(page.getByText(/Esta ação não encerra nem descarta o incidente/)).toBeVisible();
  await page.getByRole('button', { name: 'Confirmar exclusão da imagem', exact: true }).click();
  await expect(page.getByText('Imagem excluída.', { exact: true })).toBeVisible();
  await expect(page.getByAltText('Evidência pontual do evento')).toHaveCount(0);
  const retry = await request.post(`${apiUrl}/edge/events/${published.eventId}/snapshot`, {
    headers: { Authorization: `Bearer ${fixture.credential.token}`, 'Content-Type': 'image/jpeg' },
    data: await syntheticJpeg(),
  });
  expect(retry.status()).toBe(410);
  const audits = await request.get(`${apiUrl}/audit?incidentId=${published.incidentId}`, {
    headers: fixture.headers,
  });
  expect((await audits.json()).items.some((a) => a.action === 'SNAPSHOT_DELETED')).toBe(true);
  await submit(page, 'RECOGNIZE');
  await expect(page.getByText('Reconhecido', { exact: true }).first()).toBeVisible();
});

test('DirectML real FILE → incidente → aviso → revisão automatizada persistida', async ({
  page,
  request,
  fixture,
}) => {
  test.skip(!process.env.RADAR_DIRECTML_PROTOCOL, 'Protocolo privado e GPU opt-in obrigatórios.');
  test.setTimeout(180000);
  const directory = `.local/directml-integration-e2e/${randomUUID()}`;
  await mkdir(directory, { recursive: true });
  const credentialFile = `${directory}/worker.json`;
  await writeFile(
    credentialFile,
    JSON.stringify({
      cameraId: fixture.camera.id,
      apiUrl,
      deviceToken: fixture.credential.token,
    }),
  );
  async function python(args) {
    const child = spawn(
      'uv',
      [
        'run',
        '--project',
        process.env.RADAR_DIRECTML_RUNTIME_PROJECT || 'experiments/directml',
        '--frozen',
        'python',
        ...args,
      ],
      {
        env: process.env,
        windowsHide: true,
        stdio: ['ignore', 'pipe', 'pipe'],
      },
    );
    let output = '',
      errors = '';
    child.stdout.on('data', (x) => {
      output += x;
    });
    child.stderr.on('data', (x) => {
      errors += x;
    });
    const code = await new Promise((resolve, reject) => {
      child.once('error', reject);
      child.once('exit', resolve);
    });
    await writeFile(`${directory}/worker-${randomUUID()}.log`, output + errors);
    expect(code, 'Worker DirectML encerrou com erro; consulte os registros privados.').toBe(0);
    return JSON.parse(output);
  }
  const results = [];
  for (const caseId of ['intake16-03', 'chair08-02']) {
    const prepared = await python([
      'scripts/validation/prepare-directml-replay.py',
      '--protocol',
      process.env.RADAR_DIRECTML_PROTOCOL,
      '--case',
      caseId,
      '--camera-id',
      fixture.camera.id,
      '--credential',
      credentialFile,
      '--output',
      `${directory}/${caseId}`,
    ]);
    const result = await python(['scripts/run-edge.py', 'run', '--config', prepared.config]);
    expect(result.status).toBe('ok');
    expect(result.mode).toBe('REPLAY');
    expect(result.model.delegate).toBe('DIRECTML');
    expect(result.model.executor.operatorProfile.gpuComputeProven).toBe(true);
    expect(result.health.captureState).toBe('ENDED');
    expect(result.health.outboxPending).toBe(0);
    expect(result.framesSaved).toBe(false);
    const rows = (await readFile(result.decisionExport.path, 'utf8'))
      .trim()
      .split('\n')
      .map(JSON.parse);
    const ds = rows.filter((x) => x.recordType === 'DECISION').map((x) => x.timestampMs);
    const ps = rows.filter((x) => x.recordType === 'PROCESSING_PROFILE').map((x) => x.timestampMs);
    expect(ps).toEqual(ds);
    expect(ds.length).toBeGreaterThan(5);
    expect(result.temporal.generatedEvents).toBe(caseId === 'intake16-03' ? 1 : 0);
    results.push({
      caseId,
      reportPath: result.reportPath,
      model: result.model,
      events: result.temporal.generatedEvents,
      decisions: ds.length,
      pending: result.health.outboxPending,
      heartbeat: result.network.heartbeat,
    });
  }
  const incidents = await fixture.database.incident.findMany({
    where: { cameraId: fixture.camera.id },
  });
  expect(incidents).toHaveLength(1);
  const incident = incidents[0];
  expect(incident.mode).toBe('REPLAY');
  expect(incident.deliveryClass).toBe('TEST');
  expect(incident.kind).toBe('PERSON_ON_FLOOR');
  const receipt = await fixture.database.eventReceipt.findFirstOrThrow({
    where: { incidentId: incident.id },
  });
  const resend = await request.post(`${apiUrl}/edge/events`, {
    headers: { Authorization: `Bearer ${fixture.credential.token}` },
    data: receipt.payload,
  });
  expect(resend.status()).toBe(200);
  const duplicate = await resend.json();
  expect(duplicate.duplicate).toBe(true);
  expect(duplicate.incidentId).toBe(incident.id);
  expect(await fixture.database.incident.count({ where: { cameraId: fixture.camera.id } })).toBe(1);
  expect(await fixture.database.eventReceipt.count({ where: { incidentId: incident.id } })).toBe(1);
  await expect
    .poll(() =>
      fixture.database.notificationDelivery.count({
        where: { intent: { incidentId: incident.id } },
      }),
    )
    .toBe(1);
  expect(
    await fixture.database.notificationIntent.count({ where: { incidentId: incident.id } }),
  ).toBe(1);
  await login(page, fixture);
  await page.goto(`/incidentes/${incident.id}`);
  await expect(
    page.getByRole('heading', { name: 'Possível pessoa no chão', exact: true }),
  ).toBeVisible();
  await expect(page.getByText('Reprodução', { exact: true })).toBeVisible();
  await expect(page.getByText('Teste', { exact: true })).toBeVisible();
  await page.getByRole('combobox', { name: 'Ação', exact: true }).selectOption('SET_REVIEW');
  await page
    .getByRole('combobox', { name: 'Revisão humana', exact: true })
    .selectOption('PERSON_ON_FLOOR_CONFIRMED');
  const note =
    'REVISÃO AUTOMATIZADA DE TESTE DirectML/REPLAY. Não representa revisão humana do fundador.';
  await page.getByLabel('Nota', { exact: true }).fill(note);
  await page.getByRole('button', { name: 'Registrar ação', exact: true }).click();
  await expect(page.getByText('Ação registrada com sucesso.', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.locator('.timeline').getByText(note, { exact: true })).toBeVisible();
  const stored = await fixture.database.incident.findUniqueOrThrow({ where: { id: incident.id } });
  expect(stored.review).toBe('PERSON_ON_FLOOR_CONFIRMED');
  expect(stored.version).toBe(2);
  const camera = await fixture.database.camera.findUniqueOrThrow({
    where: { id: fixture.camera.id },
  });
  expect(camera.lastHeartbeat.captureState).toBe('ENDED');
  expect(camera.lastHeartbeat.outboxPending).toBe(0);
  await writeFile(
    `${directory}/verification.json`,
    JSON.stringify(
      {
        scope: 'AUTOMATED_TEST_NOT_FOUNDER_HUMAN_REVIEW',
        incidentId: incident.id,
        mode: stored.mode,
        deliveryClass: stored.deliveryClass,
        review: stored.review,
        version: stored.version,
        duplicate: duplicate.duplicate,
        notificationDeliveries: 1,
        heartbeatFinal: camera.lastHeartbeat.captureState,
        results,
      },
      null,
      2,
    ),
  );
  console.log(`DirectML: integração isolada comprovada; registros privados em ${directory}`);
});
