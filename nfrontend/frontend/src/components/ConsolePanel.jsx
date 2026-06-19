import { useState } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'

export default function ConsolePanel() {
  const { activeProjectId, setExecutionUrl } = useProject()
  const [output, setOutput] = useState('')
  const [executing, setExecuting] = useState(false)

  const execute = async () => {
    if (!activeProjectId || executing) return
    setExecuting(true)
    setOutput('🔄 Preparando ejecución...\n')
    try {
      const res = await api.post(`/projects/${activeProjectId}/execute`)
      const data = res.data

      if (data.steps && data.steps.length > 0) {
        setOutput(data.steps.join('\n'))
      }

      if (data.success && data.url) {
        setExecutionUrl(data.url)
        setOutput(prev => prev + `\n\n✅ Proyecto ejecutado correctamente.\n🔗 URL: ${data.url}\n📱 La Vista previa se actualizó automáticamente.`)
      } else if (!data.success) {
        setOutput(prev => prev + `\n\n❌ Error al ejecutar:\n${data.stderr || data.stdout || 'Error desconocido'}`)
      }
    } catch (err) {
      setOutput(prev => prev + '\n❌ Error de conexión al ejecutar.')
    } finally {
      setExecuting(false)
    }
  }

  return (
    <div className="p-6 flex flex-col h-full">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-100">🖥️ Consola de Ejecución</h2>
        <button
          onClick={execute}
          disabled={!activeProjectId || executing}
          className="bg-gradient-to-r from-green-600 to-emerald-500 hover:from-green-500 hover:to-emerald-400 text-white px-5 py-2 rounded-xl font-medium transition shadow-lg shadow-green-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {executing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Ejecutando...
            </>
          ) : (
            <>
              ▶️ Ejecutar proyecto
            </>
          )}
        </button>
      </div>
      <div className="flex-1 bg-gray-950 border border-gray-700/50 rounded-xl p-4 font-mono text-sm text-green-400 overflow-y-auto whitespace-pre-wrap">
        {output || 'Presioná "Ejecutar proyecto" para instalar dependencias y correr el backend.\n\nEl proyecto se ejecutará en http://localhost:8001.'}
      </div>
    </div>
  )
}