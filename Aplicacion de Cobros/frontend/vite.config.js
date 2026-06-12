import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://localhost:8001',
      '/clientes': 'http://localhost:8001',
      '/pagos': 'http://localhost:8001'
    }
  }
})