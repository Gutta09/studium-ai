import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    proxy: {
      // Frontend talks to relative /api — Vite forwards to FastAPI in dev
      '/api': 'http://localhost:8000',
    },
  },
})
