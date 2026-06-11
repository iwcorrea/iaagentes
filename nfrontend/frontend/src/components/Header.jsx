import { useProject } from '../context/ProjectContext'

export default function Header() {
  const { activeProjectId, projectName } = useProject()

  return (
    <header className="bg-gray-800/40 backdrop-blur-md border-b border-gray-700/30 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
          <span className="text-white text-lg">🧠</span>
        </div>
        <div>
          <h1 className="font-bold text-lg bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
            Panel de Agentes IA
          </h1>
          <p className="text-xs text-gray-500">Wilson Correa</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        {activeProjectId && (
          <span className="text-sm px-4 py-1.5 bg-blue-900/30 text-blue-300 border border-blue-500/20 rounded-full font-medium">
            {projectName || activeProjectId}
          </span>
        )}
        <span className="text-xs px-3 py-1 bg-green-900/30 text-green-300 border border-green-500/20 rounded-full">
          🟢 Operativo
        </span>
      </div>
    </header>
  )
}