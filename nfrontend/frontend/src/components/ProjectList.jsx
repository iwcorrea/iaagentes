import { useState, useEffect } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'

export default function ProjectList() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editing, setEditing] = useState(null)
  const [newName, setNewName] = useState('')
  const { activeProjectId, setActiveProjectId } = useProject()

  const fetchProjects = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.get('/api/projects')
      setProjects(res.data.projects || [])
    } catch (err) {
      setError('No se pudieron cargar los proyectos.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  const handleOpenProject = (id) => {
    setActiveProjectId(id)
  }

  const handleRename = async (id) => {
    if (!newName.trim()) return
    try {
      await api.put(`/api/projects/${id}/name`, { name: newName.trim() })
      setProjects(prev => prev.map(p => p.id === id ? { ...p, name: newName.trim() } : p))
      setEditing(null)
      setNewName('')
    } catch (err) {
      alert('Error al renombrar el proyecto.')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar este proyecto y toda su información? Esta acción no se puede deshacer.')) return
    try {
      await api.delete(`/api/projects/${id}`)
      setProjects(prev => prev.filter(p => p.id !== id))
      if (activeProjectId === id) setActiveProjectId(null)
    } catch (err) {
      alert('Error al eliminar el proyecto.')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
        <span className="ml-3 text-gray-400">Cargando proyectos...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <p className="text-red-400 mb-3">{error}</p>
        <button onClick={fetchProjects} className="bg-cyan-600/20 text-cyan-400 px-4 py-2 rounded-lg hover:bg-cyan-600/30 transition">
          Reintentar
        </button>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-white">📁 Proyectos</h2>
        <span className="text-sm text-gray-400">{projects.length} proyecto(s)</span>
      </div>
      {projects.length === 0 ? (
        <p className="text-gray-500">No hay proyectos todavía. Creá uno desde el chat.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map(proj => (
            <div
              key={proj.id}
              className={`relative bg-gray-800/60 border rounded-xl p-5 transition-all duration-300 hover:shadow-lg group ${
                activeProjectId === proj.id
                  ? 'border-cyan-500 shadow-cyan-500/20'
                  : 'border-gray-700/50 hover:border-cyan-500/40'
              }`}
            >
              <div className="flex justify-between items-start mb-3">
                {editing === proj.id ? (
                  <input
                    type="text"
                    value={newName}
                    onChange={e => setNewName(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleRename(proj.id)}
                    onBlur={() => setEditing(null)}
                    autoFocus
                    className="bg-gray-700 text-white px-2 py-1 rounded text-sm w-full"
                  />
                ) : (
                  <h3 className="font-bold text-lg text-white truncate pr-12">{proj.name}</h3>
                )}
                <div className="absolute top-3 right-3 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => { e.stopPropagation(); setEditing(proj.id); setNewName(proj.name) }}
                    className="text-gray-400 hover:text-cyan-400 text-sm p-1 rounded"
                    title="Renombrar"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(proj.id) }}
                    className="text-gray-400 hover:text-red-400 text-sm p-1 rounded"
                    title="Eliminar"
                  >
                    🗑️
                  </button>
                </div>
              </div>
              <p className="text-xs text-gray-500 font-mono mb-4">ID: {proj.id}</p>
              <button
                onClick={() => handleOpenProject(proj.id)}
                className="w-full bg-cyan-600/20 text-cyan-400 py-2 rounded-lg hover:bg-cyan-600/30 transition text-sm font-medium"
              >
                {activeProjectId === proj.id ? '✓ Proyecto activo' : 'Abrir proyecto'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}