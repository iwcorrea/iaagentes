import React from 'react';
import { User, LogOut, Code2 } from 'lucide-react';
import { getUserRole } from '../api/axios';
export default function Header({ onLogout }) {
  const role = getUserRole();
  return (
    <header className="h-14 border-b border-brand-border bg-brand-surface flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-2">
        <Code2 className="text-brand-accent" />
        <span className="font-bold text-lg">CodeOptimizer <span className="text-xs text-slate-500 font-normal">v1.0</span></span>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <User size={16} />
          <span className="capitalize">{role || 'User'}</span>
        </div>
        <button 
          onClick={onLogout}
          className="p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition"
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}