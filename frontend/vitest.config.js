import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    alias: {
      '@': fileURLToPath(new URL('./src/', import.meta.url))
    },
    include: ['**/__tests__/*.{js,tsx,ts}'],
  }
}) 