import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
export default function DashboardMaestro() {
  const [clients, setClients] = useState([]);
  const [payments, setPayments] = useState([]);
  const [newPayment, setNewPayment] = useState({
    clientId: '',
    amount: '',
    concept: '',
    date: new Date().toISOString().split('T')[0],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  // Fetch clients (users with role cliente)
  useEffect(() => {
    const fetchClients = async () => {
      try {
        const res = await api.get('/users'); // Assuming endpoint returns all users
        const clientes = res.data.filter((u) => u.role === 'cliente');
        setClients(clientes);
      } catch (err) {
        console.error('Error fetching clients', err);
      }
    };
    fetchClients();
  }, []);
  // Fetch recent payments
  useEffect(() => {
    const fetchPayments = async () => {
      try {
        const res = await api.get('/payments');
        setPayments(res.data);
      } catch (err) {
        console.error('Error fetching payments', err);
      }
    };
    fetchPayments();
  }, []);
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setNewPayment((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.post('/payments', newPayment);
      // Reset form and refresh payments
      setNewPayment({
        clientId: '',
        amount: '',
        concept: '',
        date: new Date().toISOString().split('T')[0],
      });
      const res = await api.get('/payments');
      setPayments(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al registrar pago');
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Panel de Maestro</h1>
        <nav className="space-x-4">
          <a
            href="/"
            className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded hover:bg-indigo-200 transition"
          >
            Inicio
          </a>
          <a
            href="/login"
            onClick={(e) => {
              e.preventDefault();
              localStorage.removeItem('access_token');
              localStorage.removeItem('user');
              navigate('/login', { replace: true });
            }}
            className="px-3 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition"
          >
            Cerrar sesión
          </a>
        </nav