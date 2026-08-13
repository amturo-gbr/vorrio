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
        globIgnores: [
          'assets/translation-*.js',
        ],
        runtimeCaching: [
          {
            urlPattern: /\/assets\/translation-[^/]+\.js$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'vorrio-language-packs-v1',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 365 * 24 * 60 * 60,
              },
            },
          },
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
