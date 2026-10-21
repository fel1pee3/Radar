import { defineConfig } from '@playwright/test';
if (!/^radar-e2e-[a-f0-9]{12}$/.test(process.env.RADAR_E2E_CONTAINER ?? ''))
  throw new Error('Execute pnpm.cmd test:e2e para criar recursos exclusivos.');
export default defineConfig({
  testDir: '.',
  testMatch: '*.spec.mjs',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: true,
  timeout: 60000,
  expect: { timeout: 10000 },
  reporter: 'list',
  outputDir: '../../.local/etapa03/results',
  use: {
    baseURL: process.env.RADAR_E2E_WEB_URL,
    trace: 'off',
    screenshot: 'off',
    video: 'off',
    browserName: 'chromium',
  },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 1000 } } },
    {
      name: 'mobile',
      use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true },
    },
  ],
});
