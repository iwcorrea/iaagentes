import { useState, useEffect } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'

export default function ProjectList() {
  const [projects, setProjects] = useState([])
  const { setActiveProjectId } = useProject()

  const load = async () => {
    const res = await api.get('/projects')
    const ids = res.data.projects || []
    const enriched = await Promise.all(ids.map(async (id) => {
      try {
        const nameRes = await api.get(`/projects/${id}/name`)
        return { id, name: nameRes.data.name || id }
      } catch {
        return { id, name: id }
      }
    }))
    setProjects(enriched)
  }

  useEffect(() => { load() }, [])

  const handleRename = async (id, currentName) => {
    const newName = prompt('Nuevo nombre para el proyecto:', currentName)
    if (newName && newName.trim()) {
      await api.put(`/projects/${id}/name`, { name: newName.trim() })
      setProjects(prev => prev.map(p => p.id === id ? { ...p, name: newName.trim() } : p))
    }
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-100">Proyectos generados</h2>
        <button onClick={load} className="text-blue-400 hover:text-blue-300 text-sm font-medium transition">Refrescar</button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {projects.length === 0 && (
          <div className="col-span-full text-center text-gray-500 py-20">
            <p className="text-lg">Todavía no hay proyectos.</p>
            <p className="text-sm">Usá el Chat para crear el primero.</p>
          </div>
        )}
        {projects.map(p => (
          <div key={p.id} className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-5 flex flex-col gap-4 hover:border-blue-500/30 transition-all duration-200 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl flex items-center justify-center text-xl border border-blue-500/20">
                📁
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-200 truncate">{p.name}</div>
                <div className="text-xs text-gray-500 font-mono">{p.id}</div>
              </div>
              <button onClick={() => handleRename(p.id, p.name)} className="text-gray-500 hover:text-blue-400 transition">
                ✏️
              </button>
            </div>
            <div className="flex gap-3 mt-auto">
              <button onClick={() => setActiveProjectId(p.id)} className="flex-1 bg-blue-600/20 text-blue-300 border border-blue-500/30 hover:bg-blue-600/30 text-sm py-2.5 rounded-xl font-medium transition">
                Abrir
              </button>
              <button onClick={() => setActiveProjectId(p.id)} className="flex-1 bg-cyan-600/20 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-600/30 text-sm py-2.5 rounded-xl font-medium transition">
                Ejecutar
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}