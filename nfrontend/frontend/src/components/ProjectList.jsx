import { useState, useEffect } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'

export default function ProjectList() {
  const [projects, setProjects] = useState([])
  const { setActiveProjectId } = useProject()

  const load = async () => {
    const res = await api.get('/projects')
    setProjects(res.data.projects || [])
  }

  useEffect(() => { load() }, [])

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Proyectos generados</h2>
        <button onClick={load} className="text-blue-600 dark:text-blue-400 text-sm hover:underline">Refrescar</button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.length === 0 && (
          <div className="col-span-full text-center text-gray-500 py-20">
            <p>Todavía no hay proyectos.</p>
            <p className="text-sm">Usá el Chat para crear el primero.</p>
          </div>
        )}
        {projects.map(id => (
          <div key={id} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">📁</span>
              <span className="font-mono text-sm text-blue-600 dark:text-blue-400">{id}</span>
            </div>
            <div className="flex gap-2 mt-auto">
              <button onClick={() => setActiveProjectId(id)} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm py-2 rounded-lg transition">Abrir</button>
              <button onClick={() => {
                setActiveProjectId(id)
                // Opcional: ejecutar automáticamente
              }} className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm py-2 rounded-lg transition">Ejecutar</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}