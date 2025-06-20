import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: { // Optional: configure dev server
    port: 3000, // Standard React dev port
    strictPort: true, // Exit if port is already in use
    // proxy: { // If backend is on different port during dev and needs proxying
    //   '/api': {
    //     target: 'http://localhost:8000', // Your backend address
    //     changeOrigin: true,
    //   }
    // }
  }
})
