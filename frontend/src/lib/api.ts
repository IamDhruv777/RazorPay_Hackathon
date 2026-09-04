import axios from 'axios';

const api = axios.create({
  // Use relative path to take advantage of Next.js rewrites.
  // This prevents all CORS and IP binding issues in remote workspaces.
  baseURL: '/api',
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('demo_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export default api;
