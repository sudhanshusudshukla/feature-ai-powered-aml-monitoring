import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
/// <reference types="vitest" />

export default defineConfig(({ mode }) => {
  // Load env variables including BACKEND_PORT from process.env
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        // Proxy /api to backend without rewriting path
        '/api': {
          target: `http://127.0.0.1:${env.BACKEND_PORT || 9000}`,
          changeOrigin: true,
        },
      },
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      exclude: ['e2e/**', 'node_modules/**'],
    },
  };
});
