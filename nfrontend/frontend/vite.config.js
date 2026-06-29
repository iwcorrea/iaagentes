import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Redirigir cualquier ruta antigua /projects al nuevo /api/projects
      '/projects': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/projects/, '/api/projects')
      },
      // Redirigir /api/agents, /api/skills, etc. (ya funciona, pero por completitud)
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})