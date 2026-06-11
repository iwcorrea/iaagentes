import React, { useState, useEffect } from 'react';
import { CheckCircle, Clock, AlertCircle } from 'lucide-react';
import api from '../api/axios';
export default function ImprovementsPanel({ project }) {
  const [improvements, setImprovements] = useState([]);
  useEffect(() => {
    if (project) {
      api.get(`/projects/${project.id}/improvements`)
        .then(res => setImprovements(res.data))
        .catch(err => console.error(err));
    }
  }, [project]);
  const updateStatus = async (id, status) => {
    try {
      await api.patch(`/improvements/${id}`, { status });
      setImprovements(prev => prev.map(imp => imp.id === id ? { ...imp, status } : imp));
    } catch (err) {
      console.error("Error updating status", err);
    }
  };
  return (
    <div className="h-1/2 flex flex-col bg-brand-surface">
      <div className="p-3 border-b border-brand-border font-semibold text-sm">Suggested Improvements</div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {improvements.map(imp => (
          <div key={imp.id} className="p-3 rounded-lg bg-brand-dark border border-brand-border text-sm space-y-2">
            <div className="flex justify-between items-start">
              <span className="font-medium">{imp.title}</span>
              {imp.status === 'completed' ? <CheckCircle size={14} className="text-green-500" /> : <Clock size={14} className="text-yellow-500" />}
            </div>
            <p className="text-xs text-slate-400">{imp.description}</p>
            <div className="flex gap-2 pt-2">
              <button 
                onClick={() => updateStatus(imp.id, 'completed')}
                className="text-[10px] px-2 py-1 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30"
              >
                Mark Done
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}