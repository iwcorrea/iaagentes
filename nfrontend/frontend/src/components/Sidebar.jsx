import { useState, useEffect } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'

export default function Sidebar() {
  const { activeProjectId, setActiveProjectId } = useProject()
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)

  const loadFiles = async () => {
    if (!activeProjectId) return
    setLoading(true)
    try {
      const res = await api.get(`/projects/${activeProjectId}/files`)
      setFiles(res.data.files || [])
    } catch {
      setFiles([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadFiles() }, [activeProjectId])

  return (
    <aside className="w-64 bg-gray-800/40 backdrop-blur-sm border-r border-gray-700/30 flex flex-col">
      <div className="p-4 border-b border-gray-700/30 flex justify-between items-center">
        <span className="font-semibold text-gray-200 text-sm">📁 Archivos del proyecto</span>
        <div className="flex gap-2">
          <button onClick={loadFiles} className="text-gray-400 hover:text-cyan-400 transition text-xs" title="Refrescar">
            🔄
          </button>
          <button onClick={() => setActiveProjectId(null)} className="text-gray-400 hover:text-red-400 transition text-xs" title="Cerrar proyecto">
            ✕
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {loading ? (
          <div className="text-center text-gray-500 py-8">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-cyan-400 mx-auto"></div>
            <p className="text-xs mt-2">Cargando archivos...</p>
          </div>
        ) : files.length === 0 ? (
          <div className="text-center text-gray-600 py-8">
            <p className="text-3xl mb-2">📂</p>
            <p className="text-xs">Sin archivos</p>
          </div>
        ) : (
          files.map(f => (
            <div
              key={f}
              className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs text-gray-400 hover:text-gray-200 hover:bg-gray-700/30 cursor-pointer transition truncate"
              title={f}
            >
              <span className="text-cyan-400 text-xs">📄</span>
              <span className="truncate">{f}</span>
            </div>
          ))
        )}
      </div>
    </aside>
  )
}