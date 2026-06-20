import { useState, useEffect } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'
import GuidedProjectCreator from './GuidedProjectCreator'

export default function ProjectList() {
  const [projects, setProjects] = useState([])
  const [showGuided, setShowGuided] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const { setActiveProjectId } = useProject()

  const load = async () => {
    try {
      const res = await api.get('/projects')
      setProjects(res.data.projects || [])
    } catch (err) {
      console.error('Error al cargar proyectos:', err)
    }
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (id) => {
    // Por ahora solo ocultamos (no hay endpoint DELETE)
    setProjects(prev => prev.filter(p => p.id !== id))
    setDeleteConfirm(null)
  }

  const handleProjectCreated = (projectId) => {
    setActiveProjectId(projectId)
    load()
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-gray-100">📁 Proyectos</h2>
          <p className="text-gray-400 text-sm mt-1">Administrá tus proyectos generados por IA</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowGuided(true)}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white px-5 py-2.5 rounded-xl font-medium shadow-lg transition-all duration-200 flex items-center gap-2"
          >
            <span className="text-lg">✨</span> Proyecto Guiado
          </button>
          <button
            onClick={load}
            className="bg-gray-700 hover:bg-gray-600 text-gray-300 px-4 py-2.5 rounded-xl text-sm transition"
            title="Refrescar lista"
          >
            🔄
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {projects.length === 0 ? (
          <div className="col-span-full flex flex-col items-center justify-center py-20 text-gray-500">
            <div className="text-7xl mb-4">📭</div>
            <p className="text-xl font-medium text-gray-400">No hay proyectos todavía</p>
            <p className="text-sm mt-2 text-gray-600">
              Creá uno nuevo desde el <span className="text-purple-400 font-semibold">Chat</span> o usando el <span className="text-purple-400 font-semibold">Proyecto Guiado</span>.
            </p>
          </div>
        ) : (
          projects.map(project => (
            <div
              key={project.id}
              className="group bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-5 flex flex-col gap-4 transition-all duration-300 hover:border-blue-500/40 hover:shadow-xl hover:shadow-blue-500/5"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl flex items-center justify-center text-xl border border-blue-500/20">
                    📁
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-200 group-hover:text-blue-300 transition-colors truncate max-w-[180px]">
                      {project.name}
                    </h3>
                    <p className="text-xs text-gray-500 font-mono mt-0.5">{project.id}</p>
                  </div>
                </div>
                <button
                  onClick={() => setDeleteConfirm(project.id)}
                  className="text-gray-600 hover:text-red-400 transition opacity-0 group-hover:opacity-100"
                  title="Eliminar proyecto"
                >
                  🗑️
                </button>
              </div>
              <div className="flex gap-3 mt-auto">
                <button
                  onClick={() => setActiveProjectId(project.id)}
                  className="flex-1 bg-blue-600/20 text-blue-300 border border-blue-500/30 hover:bg-blue-600/30 text-sm py-2.5 rounded-xl font-medium transition"
                >
                  Abrir
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Modal de confirmación de eliminación */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 max-w-md text-center">
            <p className="text-gray-200 mb-4">¿Eliminar el proyecto <span className="font-mono text-blue-400">{deleteConfirm}</span>?</p>
            <p className="text-sm text-gray-400 mb-6">Esta acción no se puede deshacer.</p>
            <div className="flex gap-4 justify-center">
              <button onClick={() => setDeleteConfirm(null)} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg">Cancelar</button>
              <button onClick={() => handleDelete(deleteConfirm)} className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg">Eliminar</button>
            </div>
          </div>
        </div>
      )}

      {showGuided && (
        <GuidedProjectCreator
          onClose={() => setShowGuided(false)}
          onProjectCreated={handleProjectCreated}
        />
      )}
    </div>
  )
}