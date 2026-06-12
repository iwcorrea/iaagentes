import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { LayoutDashboard, CreditCard, Bell, User, LogOut, Menu, X } from 'lucide-react';
import { useState } from 'react';
const Layout = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();
  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };
  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/payments', icon: CreditCard, label: 'Cobros' },
    { path: '/notifications', icon: Bell, label: 'Notificaciones' },
    { path: '/profile', icon: User, label: 'Perfil' },
  ];
  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Mobile Header */}
      <div className="md:hidden bg-primary-600 text-white p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">Apicobros</h1>
        <button onClick={() => setIsMenuOpen(!isMenuOpen)}>
          {isMenuOpen ? <X /> : <Menu />}
        </button>
      </div>
      {/* Sidebar */}
      <aside className={`${isMenuOpen ? 'block' : 'hidden'} md:block w-full md:w-64 bg-white border-r border-slate-200 h-screen sticky top-0`}>
        <div className="p-6 hidden md:block">
          <h1 className="text-2xl font-bold text-primary-600">Apicobros</h1>
        </div>
        <nav className="p-4 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className="flex items-center gap-3 p-3 text-slate-600 hover:bg-primary-50 hover:text-primary-600 rounded-lg transition-colors"
            >
              <item.icon size={20} />
              <span className="font-medium">{item.label}</span>
            </Link>
          ))}
          <button 
            onClick={handleLogout}
            className="w-full flex items-center gap-3 p-3 text-red-500 hover:bg-red-50 rounded-lg transition-colors mt-10"
          >
            <LogOut size={20} />
            <span className="font-medium">Cerrar Sesión</span>
          </button>
        </nav>
      </aside>
      {/* Main Content */}
      <main className="flex-1 p-4 md:p-8 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
};
export default Layout;