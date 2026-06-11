import { useState, useEffect } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'

export default function Sidebar() {
  const { activeProjectId, setActiveProjectId } = useProject()
  const [files, setFiles] = useState([])

  const loadFiles = async () => {
    if (!activeProjectId) return
    const res = await api.get(`/projects/${activeProjectId}/files`)
    setFiles(res.data.files || [])
  }

  useEffect(() => { loadFiles() }, [activeProjectId])

  return (
    <aside className="w-64 bg-gray-800/40 backdrop-blur-sm border-r border-gray-700/30 flex flex-col">
      <div className="p-4 border-b border-gray-700/30 flex justify-between items-center">
        <span className="font-semibold text-gray-200">Archivos</span>
        <button onClick={() => setActiveProjectId(null)} className="text-gray-500 hover:text-red-400 transition">
          ✕
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {files.map(f => (
          <div key={f} className="text-gray-400 hover:text-gray-200 hover:bg-gray-700/30 px-3 py-1.5 rounded-lg cursor-pointer text-sm transition truncate">
            📄 {f}
          </div>
        ))}
      </div>
    </aside>
  )
}