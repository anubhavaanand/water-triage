import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // GitHub Pages serves this project from /water-triage/, not the domain root,
  // so asset URLs must be rooted there or they 404 on the deployed site.
  base: '/water-triage/',
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true
      }
    }
  }
});
