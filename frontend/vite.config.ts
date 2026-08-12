import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        id: '/',
        name: 'Vorrio',
        short_name: 'Vorrio',
        description: 'Einkäufe, Vorräte und Produktwissen selbst hosten',
        theme_color: '#176b35',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        scope: '/',
        lang: 'de',
        icons: [
          {
            src: '/pwa-icon.png',
            sizes: '1024x1024',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        navigateFallback: '/index.html',
        globPatterns: ['**/*.{js,css,html,svg,woff2}', 'assets/**/*.{png,jpg,jpeg,webp}'],
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
