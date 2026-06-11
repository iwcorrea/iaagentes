import React, { useState, useEffect } from 'react';
import { Folder, Play, Trash2, Plus } from 'lucide-react';
import api from '../api/axios';
export default function ProjectList({ onOpenProject, notify }) {
  const [projects, setProjects] = useState([]);
  const [name, setName] = useState('');
  useEffect(() => {
    loadProjects();
  }, []);
  const loadProjects = async () => {
    try {
      const { data } = await api.get('/projects');
      setProjects(data);
    } catch (err) {
      notify('Failed to load projects', 'error');
    }
  };
  const createProject = async (e) => {
    e.preventDefault();
    try {
      await api.post('/projects', { name });
      setName('');
      loadProjects();
      notify('Project created successfully');
    } catch (err) {
      notify('Error creating project', 'error');
    }
  };
  const deleteProject = async (id) => {
    try {
      await api.delete(`/projects/${id}`);
      loadProjects();
      notify('Project deleted');
    } catch (err) {
      notify('Error deleting project', 'error');
    }
  };
  return (
    <div className="p-8 max-w-6xl mx-auto w-full">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">My Projects</h1>
        <form onSubmit={createProject} className="flex gap-2">
          <input 
            value={name}
            onChange={e => setName(e.target.value)}
            className="bg-brand-surface border border-brand-border p-2 rounded text-sm outline-none focus:border-brand-accent"
            placeholder="Project name..."
          />
          <button className="bg-brand-accent p-2 rounded hover:bg-blue-600 transition"><Plus size={20} /></button>
        </form>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {projects.map(p => (
          <div key={p.id} className="bg-brand-surface border border-brand-border p-4 rounded-xl hover:border-brand-accent transition group">
            <div className="flex items-center gap-3 mb-4">
              <Folder className="text-yellow-500" />
              <span className="font-semibold truncate">{p.name}</span>
            </div>
            <div className="flex justify-end gap-2">
              <button 
                onClick={() => onOpenProject(p)}
                className="flex items-center gap-1 text-xs bg-brand-accent px-3 py-1 rounded hover:bg-blue-600 transition"
              >
                <Play size={12} /> Open
              </button>
              <button 
                onClick={() => deleteProject(p.id)}
                className="p-1 text-slate-500 hover:text-red-400 transition"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}