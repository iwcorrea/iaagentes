import React, { useState, useEffect } from 'react';
import { Folder, FileText, Plus, ChevronDown } from 'lucide-react';
import api from '../api/axios';
export default function Sidebar({ onSelectProject, activeProject, onSelectFile, selectedFile }) {
  const [files, setFiles] = useState([]);
  useEffect(() => {
    if (activeProject) {
      loadFiles();
    } else {
      setFiles([]);
    }
  }, [activeProject]);
  const loadFiles = async () => {
    try {
      const { data } = await api.get(`/projects/${activeProject.id}/files`);
      setFiles(data);
    } catch (err) {
      console.error("Error loading files", err);
    }
  };
  return (
    <aside className="w-64 border-r border-brand-border bg-brand-surface flex flex-col">
      <div className="p-4 flex justify-between items-center">
        <span className="text-xs font-semibold uppercase text-slate-500">Explorer</span>
        <button className="p-1 hover:bg-brand-border rounded"><Plus size={14} /></button>
      </div>
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {activeProject ? (
          <div className="px-2">
            <div className="flex items-center gap-2 p-2 text-sm font-medium cursor-pointer">
              <ChevronDown size={14} />
              <Folder size={14} className="text-yellow-500" />
              <span>{activeProject.name}</span>
            </div>
            <div className="ml-4 mt-1 space-y-1">
              {files.map(file => (
                <div 
                  key={file.id} 
                  onClick={() => onSelectFile(file)}
                  className={`flex items-center gap-2 p-2 text-sm cursor-pointer rounded hover:bg-brand-border transition ${selectedFile?.id === file.id ? 'bg-brand-border text-brand-accent' : ''}`}
                >
                  <FileText size={14} />
                  <span className="truncate">{file.filename}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-4 text-xs text-slate-500 italic">Select a project to view files</div>
        )}
      </div>
    </aside>
  );
}