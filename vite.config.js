import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 8081,
    strictPort: true,
    allowedHosts: ['.loca.lt'],
    proxy: {
      '/api': 'http://127.0.0.1:3001',
    },
  },
})
