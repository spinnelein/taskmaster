import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Function to get backend port from config file
function getBackendPort() {
  try {
    const configPath = path.resolve(__dirname, '../port_config.json');
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      return config.backend_port || 8000;
    }
  } catch (error) {
    console.log('Could not read port config, using default');
  }
  return process.env.VITE_BACKEND_PORT || 8000;
}

const backendPort = getBackendPort();
const backendUrl = `http://localhost:${backendPort}`;

console.log(`Vite proxy configured for backend at ${backendUrl}`);

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/health': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/docs': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/port_config.json': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true,
        rewrite: () => '../port_config.json'
      }
    }
  }
})
