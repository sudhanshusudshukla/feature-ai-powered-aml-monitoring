import { defineConfig } from '@playwright/test';

const backendPort = process.env.E2E_BACKEND_PORT ?? '9000';
const frontendPort = process.env.E2E_FRONTEND_PORT ?? '5173';
const pythonBin = process.env.E2E_PYTHON ?? 'python';
const databaseUrl = process.env.E2E_DATABASE_URL ?? 'sqlite:///./e2e.db';

export default defineConfig({
  testDir: './e2e',
  timeout: Number(process.env.E2E_TEST_TIMEOUT ?? 30_000),
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    actionTimeout: Number(process.env.E2E_ACTION_TIMEOUT ?? 10_000),
    navigationTimeout: Number(process.env.E2E_NAVIGATION_TIMEOUT ?? 15_000),
  },
  retries: 0,
  workers: 1,
  webServer: [
    {
      command: `cd ../backend && ${pythonBin} -m alembic upgrade head && ${pythonBin} -m app.seed && ${pythonBin} -m uvicorn app.main:app --host 127.0.0.1 --port ${backendPort}`,
      url: `http://127.0.0.1:${backendPort}/health`,
      reuseExistingServer: false,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
      cwd: '../backend',
      env: {
        DATABASE_URL: databaseUrl,
      },
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort} --strictPort`,
      url: `http://127.0.0.1:${frontendPort}`,
      reuseExistingServer: false,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        BACKEND_PORT: backendPort,
      },
    },
  ],
});
