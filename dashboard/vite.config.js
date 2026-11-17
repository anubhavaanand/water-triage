import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Default to '/' (relative-rooted) so the app works when served from any path
// (Render, Docker, local HTTP server). GitHub Pages uses /water-triage/ as
// base, so set BASE_PATH env var or run: BASE_PATH=/water-triage/ npm run build
const basePath = process.env.BASE_PATH || '/';

// Backend listens on 8000 (see docker-compose.yml and
// `uv run uvicorn backend.app.main:app --port 8000`). Override for a
// different host or port without editing this file:
//   VITE_API_BASE=http://127.0.0.1:9000 npm run dev
const apiTarget = process.env.VITE_API_BASE || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  base: basePath,
  server: {
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true
      }
    }
  }
});
