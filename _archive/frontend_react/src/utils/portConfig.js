// Port configuration reader for frontend
// NO EMOJIS

import axios from 'axios';

class PortConfigReader {
  constructor() {
    this.cachedPort = null;
    this.lastCheck = null;
    this.checkInterval = 5000; // Check every 5 seconds
  }

  async getBackendPort() {
    const now = Date.now();
    
    // Use cached port if recent
    if (this.cachedPort && this.lastCheck && (now - this.lastCheck) < this.checkInterval) {
      return this.cachedPort;
    }

    try {
      // Try to read port config file
      const response = await axios.get('/port_config.json', {
        timeout: 1000,
        validateStatus: (status) => status < 500
      });
      
      if (response.data && response.data.backend_port) {
        this.cachedPort = response.data.backend_port;
        this.lastCheck = now;
        return this.cachedPort;
      }
    } catch (error) {
      // Ignore errors, fall back to defaults
    }

    // Fall back to environment variable or default
    const envPort = import.meta.env.VITE_API_PORT;
    if (envPort) {
      return parseInt(envPort);
    }

    // Default port
    return 8000;
  }

  getBackendUrl() {
    // For now, return the environment variable URL if set
    if (import.meta.env.VITE_API_URL) {
      return import.meta.env.VITE_API_URL;
    }
    
    // Default to port 8000
    return 'http://localhost:8000/api';
  }

  async getBackendUrlDynamic() {
    const port = await this.getBackendPort();
    return `http://localhost:${port}/api`;
  }
}

export const portConfig = new PortConfigReader();
export default portConfig;