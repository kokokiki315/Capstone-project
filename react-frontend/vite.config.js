import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,  // 🟢 THIS is the magic line that exposes it to Wi-Fi
    port: 5173,  // This ensures the port stays the same
  }
})