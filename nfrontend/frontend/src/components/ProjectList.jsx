import React, { useState } from 'react';
import { useProject } from '../context/ProjectContext';
import { Folder, Plus, Loader2 } from 'lucide-react';

const ProjectList = () => {
  const { projects, selectedProject, selectProject, loading, fetchProjects, createProject } = useProject();
  const [showCreate, setShowCreate] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [creating, setCreating] = useState(false);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!prompt.trim() || creating) return;
    setCreating(true);
    try {
      await createProject(prompt);
      setPrompt('');
      setShowCreate(false);
    } catch (error) {
      console.error('Error creating project:', error);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="h-full bg-white rounded-lg shadow-sm p-4 overflow-y-auto">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-700">Proyectos</h2>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="p-1.5 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
          title="Nuevo proyecto"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="mb-4">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe tu proyecto..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={creating}
          />
          <button
            type="submit"
            disabled={creating || !prompt.trim()}
            className="mt-2 w-full px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:bg-gray-400 transition-colors text-sm"
          >
            {creating ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Crear'}
          </button>
        </form>
      )}

      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : projects.length === 0 ? (
        <p className="text-gray-500 text-sm text-center py-8">No hay proyectos. Crea uno nuevo.</p>
      ) : (
        <ul className="space-y-2">
          {projects.map((project) => (
            <li key={project.id}>
              <button
                onClick={() => selectProject(project)}
                className={`w-full text-left px-3 py-2 rounded-md transition-colors flex items-center gap-2 ${
                  selectedProject?.id === project.id
                    ? 'bg-blue-100 text-blue-700 border border-blue-300'
                    : 'hover:bg-gray-100 text-gray-700'
                }`}
              >
                <Folder className="w-4 h-4 flex-shrink-0" />
                <span className="truncate text-sm">{project.name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ProjectList;