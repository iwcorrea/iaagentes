import React from 'react';
import { ExternalLink } from 'lucide-react';
export default function PreviewPanel({ project }) {
  if (!project) return <div className="w-64 bg-brand-surface border-l border-brand-border p-4 text-xs text-slate-500">No project selected</div>;
  return (
    <div className="w-64 border-l border-brand-border bg-brand-surface flex flex-col">
      <div className="p-3 border-b border-brand-border flex justify-between items-center">
        <span className="text-sm font-semibold">Live Preview</span>
        <a href="http://localhost:8001" target="_blank" rel="noreferrer" className="p-1 hover:bg-brand-border rounded">
          <ExternalLink size={14} />
        </a>
      </div>
      <div className="flex-1 bg-white">
        <iframe 
          src="http://localhost:8001" 
          className="w-full h-full border-none"
          title="Preview"
        />
      </div>
    </div>
  );
}