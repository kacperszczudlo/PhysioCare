/**
 * @file vitest.config.ts
 * @description Konfiguracja środowiska uruchomieniowego Vitest dla aplikacji mobilnej z mapowaniem ścieżek `@/*`.
 */

import path from 'node:path'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  test: {
    environment: 'node',
    globals: true,
  },
})
