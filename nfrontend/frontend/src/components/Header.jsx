import { useProject } from '../context/ProjectContext'

export default function Header() {
  const { activeProjectId, projectName } = useProject()

  return (
    <header className="bg-gray-800/60 backdrop-blur-md border-b border-gray-700/30 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <span className="text-white text-lg">🧠</span>
        </div>
        <div>
          <h1 className="font-bold text-lg bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
            Panel de Agentes IA
          </h1>
          <p className="text-xs text-gray-500">Wilson Correa</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        {activeProjectId && (
          <span className="text-sm px-4 py-1.5 bg-cyan-900/20 text-cyan-300 border border-cyan-500/20 rounded-full font-medium">
            {projectName || activeProjectId}
          </span>
        )}
        <span className="text-xs px-3 py-1 bg-green-900/20 text-green-300 border border-green-500/20 rounded-full flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
          Operativo
        </span>
      </div>
    </header>
  )
}