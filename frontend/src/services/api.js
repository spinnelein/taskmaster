// API service configuration
// NO EMOJIS
import axios from 'axios';

// Determine backend URL based on environment
const getBackendUrl = () => {
  // In development, use specific backend port
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_URL || 'http://localhost:8002/api';
  }
  // In production, assume backend is on same domain
  return '/api';
};

const API_BASE_URL = getBackendUrl();

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Handle specific error statuses
      if (error.response.status === 404) {
        console.error('Resource not found');
      } else if (error.response.status === 500) {
        console.error('Server error');
      }
    }
    return Promise.reject(error);
  }
);

export const api = apiClient;
export default apiClient;