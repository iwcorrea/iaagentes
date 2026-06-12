import React from 'react';
import { TrendingUp, Users, DollarSign, Activity } from 'lucide-react';
const StatCard = ({ title, value, icon: Icon, color }) => (
  <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center gap-4">
    <div className={`p-3 rounded-lg ${color}`}>
      <Icon className="text-white" size={24} />
    </div>
    <div>
      <p className="text-sm text-slate-500">{title}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  </div>
);
const Dashboard = () => {
  return (
    <div className="space-y-8">
      <header>
        <h2 className="text-3xl font-bold text-slate-800">Panel de Control</h2>
        <p className="text-slate-500">Resumen general de tus cobros hoy</p>
      </header>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Cobrado" value="$12,450.00" icon={DollarSign} color="bg-green-500" />
        <StatCard title="Transacciones" value="142" icon={Activity} color="bg-blue-500" />
        <StatCard title="Clientes Activos" value="85" icon={Users} color="bg-purple-500" />
        <StatCard title="Crecimiento" value="+12.5%" icon={TrendingUp} color="bg-orange-500" />
      </div>
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
        <h3 className="text-lg font-semibold mb-4">Últimos Movimientos</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-slate-400 text-sm border-b border-slate-100">
                <th className="pb-3 font-medium">Cliente</th>
                <th className="pb-3 font-medium">Fecha</th>
                <th className="pb-3 font-medium">Monto</th>
                <th className="pb-3 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {[
                { name: 'Juan Pérez', date: '2023-10-24', amount: '$45.00', status: 'Completado' },
                { name: 'María García', date: '2023-10-24', amount: '$120.00', status: 'Pendiente' },
                { name: 'Carlos Ruiz', date: '2023-10-23', amount: '$30.00', status: 'Completado' },
                { name: 'Ana López', date: '2023-10-23', amount: '$200.00', status: 'Completado' },
              ].map((row, i) => (
                <tr key={i} className="text-sm hover:bg-slate-50 transition-colors">
                  <td className="py-4 font-medium">{row.name}</td>
                  <td className="py-4 text-slate-500">{row.date}</td>
                  <td className="py-4 font-semibold">{row.amount}</td>
                  <td className="py-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${row.status === 'Completado' ? 'bg-green-100 text-green-600' : 'bg-yellow-100 text-yellow-600'}`}>
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default Dashboard;