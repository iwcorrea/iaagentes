import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, MessageSquare, Settings, Users, FolderGit2 } from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const links = [
    { to: '/', icon: Home, label: 'Dashboard' },
    { to: '/projects', icon: FolderGit2, label: 'Proyectos' },
    { to: '/agents', icon: Users, label: 'Agentes' },
    { to: '/settings', icon: Settings, label: 'Configuración' },
  ];

  return (
    <aside className="w-64 bg-white shadow-md flex flex-col">
      <div className="p-4 border-b">
        <h1 className="text-xl font-bold text-gray-800">AI Ecosystem</h1>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {links.map(({ to, icon: Icon, label }) => (
          <Link
            key={to}
            to={to}
            className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
              location.pathname === to
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <Icon className="w-5 h-5" />
            <span>{label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;