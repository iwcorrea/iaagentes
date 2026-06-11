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
    <div className="p-4 flex flex-col h-full">
      <button onClick={execute} className="self-start bg-green-600 text-white px-4 py-2 rounded-lg mb-4">Ejecutar proyecto</button>
      <pre className="flex-1 bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto font-mono text-sm">{output || 'Presioná Ejecutar para ver la salida.'}</pre>
    </div>
  )
}