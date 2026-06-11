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
    <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col text-sm">
      <div className="p-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
        <span className="font-medium">Archivos</span>
        <button onClick={() => setActiveProjectId(null)} className="text-gray-400 hover:text-red-500">
          ✕
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {files.map(f => (
          <div key={f} className="hover:bg-gray-100 dark:hover:bg-gray-700 px-2 py-1 rounded cursor-pointer truncate">
            📄 {f}
          </div>
        ))}
      </div>
    </aside>
  )
}