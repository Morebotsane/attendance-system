import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: command === 'serve' ? {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
        secure: false,
      }
    } : {},
  },
  build: {
    outDir: 'dist',
  }
}))