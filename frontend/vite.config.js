// vite.config.js
// Vite is the build tool + dev server for our React app (faster than CRA)
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],  // enables JSX transpilation and React Fast Refresh
  server: {
    port: 5173,        // dev server runs on localhost:5173
    proxy: {
      // During development, "/api" requests get forwarded to our FastAPI backend
      // This avoids CORS issues in development (acts like a middleman)
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})