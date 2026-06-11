import { useProject } from '../context/ProjectContext'

export default function Header() {
  const { activeProjectId } = useProject()

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-2 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="text-xl">🧠</span>
        <h1 className="font-bold text-lg">Panel de Agentes IA de Wilson</h1>
      </div>
      <div className="text-xs text-gray-500">
        {activeProjectId ? `Proyecto: ${activeProjectId}` : 'Sin proyecto abierto'}
      </div>
    </header>
  )
}