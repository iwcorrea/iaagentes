import { useState } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'

export default function ConsolePanel() {
  const { activeProjectId } = useProject()
  const [output, setOutput] = useState('')

  const execute = async () => {
    if (!activeProjectId) return
    setOutput('Ejecutando...')
    const res = await api.post(`/projects/${activeProjectId}/execute`)
    const data = res.data
    setOutput(data.stdout || data.stderr || 'Sin salida')
  }

  return (
    <div className="p-6 flex flex-col h-full">
      <button onClick={execute} className="self-start bg-gradient-to-r from-green-600 to-emerald-500 text-white px-6 py-2.5 rounded-xl font-medium mb-4 shadow-lg shadow-green-500/20 hover:from-green-500 hover:to-emerald-400 transition">
        Ejecutar proyecto
      </button>
      <pre className="flex-1 bg-gray-900/80 border border-gray-700/50 text-green-400 p-4 rounded-xl overflow-auto font-mono text-sm">
        {output || 'Presioná Ejecutar para ver la salida.'}
      </pre>
    </div>
  )
}