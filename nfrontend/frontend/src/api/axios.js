import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',  // sin /api, para poder usar tanto rutas con /api como sin él
  timeout: 300000,
});

// Interceptor para asegurar que todas las rutas tengan el prefijo /api
api.interceptors.request.use(config => {
  // Si la URL no comienza con /api/ ni es una ruta especial, le anteponemos /api
  if (!config.url.startsWith('/api/') && !config.url.startsWith('/v1/') && config.url !== '/') {
    config.url = `/api${config.url}`;
  }
  return config;
});

export default api;