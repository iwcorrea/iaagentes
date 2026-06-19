import { useProject } from '../context/ProjectContext'

export default function PreviewPanel() {
  const { activeProjectId } = useProject()

  if (!activeProjectId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <div className="text-6xl mb-4">👁️</div>
        <p className="text-lg font-medium text-gray-400">Sin proyecto abierto</p>
        <p className="text-sm text-gray-600 mt-1">Abrí un proyecto y ejecutalo para ver la vista previa.</p>
      </div>
    )
  }

  return (
    <div className="h-full p-4">
      <div className="bg-gray-900/50 border border-gray-700/50 rounded-xl overflow-hidden h-full flex items-center justify-center">
        <iframe
          src="http://localhost:8001"
          className="w-full h-full"
          sandbox="allow-scripts allow-same-origin"
          title="Vista previa del proyecto"
          onError={(e) => { e.target.style.display = 'none'; }}
        />
        <div className="absolute text-gray-600 text-sm pointer-events-none">
          {!activeProjectId && 'El proyecto no se ha ejecutado aún.'}
        </div>
      </div>
    </div>
  )
}