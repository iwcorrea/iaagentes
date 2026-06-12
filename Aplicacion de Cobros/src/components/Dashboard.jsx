import { useState, useEffect } from 'react'
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8001',
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
})

export default function Dashboard({ user, onLogout }) {
  const [clients, setClients] = useState([])
  const [payments, setPayments] = useState([])
  const [form, setForm] = useState({ client_id: '', amount: '', description: '' })

  const loadClients = async () => {
    const res = await api.get('/clientes')
    setClients(res.data)
  }

  const loadPayments = async () => {
    const res = await api.get('/pagos/report')
    setPayments(res.data)
  }

  useEffect(() => {
    loadClients()
    loadPayments()
  }, [])

  const handlePayment = async (e) => {
    e.preventDefault()
    try {
      await api.post('/pagos', { ...form, amount: parseFloat(form.amount) })
      setForm({ client_id: '', amount: '', description: '' })
      loadPayments()
    } catch (err) {
      alert('Error al registrar pago')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold text-indigo-600">Apicobros</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-600">{user?.full_name} ({user?.role})</span>
          <button onClick={onLogout} className="bg-red-500 text-white px-3 py-1 rounded text-sm">Salir</button>
        </div>
      </header>
      <main className="p-6 max-w-4xl mx-auto space-y-6">
        {user?.role === 'admin' && (
          <div className="bg-white p-4 rounded-xl shadow">
            <h2 className="font-bold mb-3">Registrar Pago</h2>
            <form onSubmit={handlePayment} className="flex gap-3 flex-wrap">
              <select value={form.client_id} onChange={e => setForm({...form, client_id: e.target.value})}
                className="border rounded-lg px-3 py-2" required>
                <option value="">Cliente</option>
                {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <input type="number" placeholder="Monto" value={form.amount} onChange={e => setForm({...form, amount: e.target.value})}
                className="border rounded-lg px-3 py-2" required />
              <input type="text" placeholder="Descripción" value={form.description} onChange={e => setForm({...form, description: e.target.value})}
                className="border rounded-lg px-3 py-2" />
              <button type="submit" className="bg-indigo-600 text-white px-4 py-2 rounded-lg">Registrar</button>
            </form>
          </div>
        )}
        <div className="bg-white p-4 rounded-xl shadow">
          <h2 className="font-bold mb-3">Últimos Pagos</h2>
          <table className="w-full text-sm">
            <thead><tr><th className="text-left">Cliente</th><th>Monto</th><th>Fecha</th></tr></thead>
            <tbody>
              {payments.map(p => (
                <tr key={p.id}>
                  <td>{clients.find(c => c.id === p.client_id)?.name || 'N/A'}</td>
                  <td>${p.amount}</td>
                  <td>{new Date(p.date).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}