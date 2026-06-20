import { useProject } from '../context/ProjectContext'
import api from '../api/axios'
import { useState, useEffect } from 'react'

export default function ProjectDashboard() {
  const { activeProjectId, projectName, projectStats, executionUrl } = useProject()
  const [auditIssues, setAuditIssues] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (activeProjectId) {
      setLoading(true)
      api.get(`/projects/${activeProjectId}/audit`)
        .then(res => setAuditIssues(res.data.issues || []))
        .catch(() => setAuditIssues([]))
        .finally(() => setLoading(false))
    }
  }, [activeProjectId])

  const executeProject = async () => {
    await api.post(`/projects/${activeProjectId}/execute`)
    // Actualizar URL de ejecución
    const { setExecutionUrl } = useProject()
    setExecutionUrl('http://localhost:8001')
  }

  if (!activeProjectId) return null

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-3xl font-bold text-white">📊 Dashboard del Proyecto</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Tarjeta de Resumen */}
        <div className="bg-gray-800/60 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-cyan-400 mb-4">Resumen</h3>
          <div className="space-y-2 text-sm">
            <p><span className="text-gray-400">Nombre:</span> {projectName}</p>
            <p><span className="text-gray-400">ID:</span> <span className="font-mono text-xs text-cyan-300">{activeProjectId}</span></p>
            <p><span className="text-gray-400">Archivos:</span> {projectStats.files}</p>
            {projectStats.lastGeneration && (
              <p><span className="text-gray-400">Última modificación:</span> {new Date(projectStats.lastGeneration).toLocaleString()}</p>
            )}
          </div>
        </div>

        {/* Auditoría */}
        <div className="bg-gray-800/60 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-yellow-400 mb-4">Auditoría</h3>
          {loading ? (
            <p className="text-gray-500 text-sm">Cargando...</p>
          ) : auditIssues.length === 0 ? (
            <p className="text-green-400 text-sm">✅ Sin problemas detectados.</p>
          ) : (
            <div className="space-y-2 text-sm max-h-48 overflow-y-auto">
              {auditIssues.map((issue, i) => (
                <div key={i} className="text-red-400 border-l-2 border-red-500 pl-2">{issue}</div>
              ))}
            </div>
          )}
        </div>

        {/* Acciones rápidas */}
        <div className="bg-gray-800/60 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-purple-400 mb-4">Acciones</h3>
          <div className="flex flex-col gap-3">
            <button onClick={executeProject} className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg text-sm transition">▶️ Ejecutar proyecto</button>
            {executionUrl && (
              <a href={executionUrl} target="_blank" rel="noopener noreferrer" className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm text-center transition">👁️ Ver vista previa</a>
            )}
            <button onClick={() => window.location.href = '/dashboard'} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm transition">🔄 Refrescar datos</button>
          </div>
        </div>
      </div>
    </div>
  )
}