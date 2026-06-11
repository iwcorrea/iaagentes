import React, { useState } from 'react';
import { Terminal } from 'lucide-react';
import api from '../api/axios';
export default function ConsolePanel({ project }) {
  const [output, setOutput] = useState('Ready...');
  const execute = async () => {
    try {
      const { data } = await api.post(`/projects/${project.id}/execute`);
      setOutput(data.output);
    } catch (err) {
      setOutput(`Error: ${err.response?.data?.detail || 'Execution failed'}`);
    }
  };
  return (
    <div className="h-48 border-t border-brand-border bg-black text-green-400 font-mono text-xs p-3 flex flex-col">
      <div className="flex justify-between items-center mb-2 text-slate-500">
        <div className="flex items-center gap-2"><Terminal size={12} /> Console</div>
        <button onClick={execute} className="text-[10px] bg-slate-800 px-2 py-1 rounded hover:bg-slate-700">Run Project</button>
      </div>
      <div className="flex-1 overflow-y-auto custom-scrollbar whitespace-pre-wrap">
        {output}
      </div>
    </div>
  );
}