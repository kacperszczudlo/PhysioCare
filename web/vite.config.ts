import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 0,
        proxyTimeout: 0,
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes, req) => {
            if (req.url?.includes('/me/events')) {
              proxyRes.headers['cache-control'] = 'no-cache, no-transform'
              proxyRes.headers['x-accel-buffering'] = 'no'
              // unikaj gzip buforującego stream
              delete proxyRes.headers['content-encoding']
            }
          })
        },
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
