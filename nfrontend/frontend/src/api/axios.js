import axios from 'axios';

const api = axios.create({
  baseURL: '/',  // Usa el proxy de Vite
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

export default api;