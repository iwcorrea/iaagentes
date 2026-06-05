import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
export default function AuthForm() {
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  const [form, setForm] = useState({
    email: '',
    password: '',
    name: '',
    role: 'cliente',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      if (mode === 'login') {
        const res = await api.post('/auth/token', {
          username: form.email,
          password: form.password,
        });
        const { access_token, user } = res.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('user', JSON.stringify(user));
        navigate(user.role === 'maestro' ? '/maestro/dashboard' : '/cliente/dashboard', { replace: true });
      } else {
        const res = await api.post('/auth/register', {
          email: form.email,
          password: form.password,
          name: form.name,
          role: form.role,
        });
        const { access_token, user } = res.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('user', JSON.stringify(user));
        navigate(user.role === 'maestro' ? '/maestro/dashboard' : '/cliente/dashboard', { replace: true });
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md space-y-6 p-6 bg-white rounded-lg shadow-md">
        <h2 className="text-center text-2xl font-bold">{mode === 'login' ? 'Iniciar sesión' : 'Crear cuenta'}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              Correo electrónico
            </label>
            <input
              id="email"
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          {mode === 'register' && (
            <>
              <div>
                <label htmlFor="name" className="block text-sm font-medium mb-1">
                  Nombre completo
                </label>
                <input
                  id="name"
                  type="text"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label htmlFor="role" className="block text-sm font-medium mb-1">
                  Rol
                </label>
                <select
                  id="role"
                  name="role"
                  value={form.role}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="maestro">Maestro (Administrador)</option>
                  <option value="cliente">Cliente</option>
                </select>
              </div>
            </>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center px-4 py-2 bg-indigo-600 text-white font-medium rounded-md disabled:opacity-50 transition-colors"
          >
            {loading ? 'Procesando...' : mode === 'login' ? 'Iniciar sesión' : 'Crear cuenta'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-600">
          {mode === 'login' ? (
            <>
              ¿No tienes cuenta?{' '}
              <button
                type="button"
                onClick={() => setMode('register')}
                className="font-medium text-indigo-600 hover:text-indigo-500"
              >
                Regístrate
              </button>
            </>
          ) : (
            <>
              Ya tienes cuenta?{' '}
              <button
                type="button"
                onClick={() => setMode('login')}
                className="font-medium text-indigo-600 hover:text-indigo-500"
              >
                Inicia sesión
              </button>
            </>
          )}
        </p>
        {error && (
          <p className="text-center text-sm text-red-600 bg-red-50 p-3 rounded">{error}</p>
        )}
      </div>
    </div>
  );
}