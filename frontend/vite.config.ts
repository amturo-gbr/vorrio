import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  build: {
    manifest: true,
  },
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: false,
      workbox: {
        navigateFallback: '/index.html',
        globPatterns: [
          '**/*.{js,css,html,svg,woff2,webmanifest,png}',
        ],
        importScripts: ['/push-worker.js'],
      },
    }),
  ],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8080',
    },
  },
})
