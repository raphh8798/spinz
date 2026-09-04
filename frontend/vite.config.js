import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default {
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:5000" }
  }
}
