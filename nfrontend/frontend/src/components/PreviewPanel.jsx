import { useProject } from '../context/ProjectContext'

export default function PreviewPanel() {
  const { activeProjectId, executionUrl } = useProject()

  if (!activeProjectId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <div className="text-6xl mb-4">👁️</div>
        <p className="text-lg font-medium text-gray-400">Sin proyecto abierto</p>
        <p className="text-sm text-gray-600 mt-1">Abrí un proyecto y ejecutalo para ver la vista previa.</p>
      </div>
    )
  }

  if (!executionUrl) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <div className="text-6xl mb-4">🚀</div>
        <p className="text-lg font-medium text-gray-400">Proyecto no ejecutado</p>
        <p className="text-sm text-gray-600 mt-1">Andá a la pestaña <span className="text-green-400 font-semibold">Consola</span> y presioná "Ejecutar proyecto".</p>
      </div>
    )
  }

  return (
    <div className="h-full p-4">
      <div className="bg-gray-900/50 border border-gray-700/50 rounded-xl overflow-hidden h-full">
        <iframe
          src={executionUrl}
          className="w-full h-full"
          sandbox="allow-scripts allow-same-origin"
          title="Vista previa del proyecto"
        />
      </div>
    </div>
  )
}