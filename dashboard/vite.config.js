import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Default to '/' (relative-rooted) so the app works when served from any path
// (Render, Docker, local HTTP server). GitHub Pages uses /water-triage/ as
// base, so set BASE_PATH env var or run: BASE_PATH=/water-triage/ npm run build
const basePath = process.env.BASE_PATH || '/';

export default defineConfig({
  plugins: [react()],
  base: basePath,
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true
      }
    }
  }
});
