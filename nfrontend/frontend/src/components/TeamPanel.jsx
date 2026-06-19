import { useState, useEffect, useCallback } from 'react'
import api from '../api/axios'

export default function TeamPanel() {
  const [teams, setTeams] = useState([])
  const [tools, setTools] = useState([])
  const [coreModules, setCoreModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedSections, setExpandedSections] = useState({ tools: false, core: false })

  const loadData = useCallback(async () => {
    try {
      const res = await api.get('/api/agents')
      setTeams(res.data.teams || [])
      setTools(res.data.tools || [])
      setCoreModules(res.data.core_modules || [])
    } catch (err) {
      console.error('Error al cargar datos del equipo:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 10000)
    return () => clearInterval(interval)
  }, [loadData])

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
        <span className="ml-3 text-gray-400">Cargando centro de control...</span>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-8">
      {/* Cabecera */}
      <div>
        <h2 className="text-3xl font-bold text-white flex items-center gap-3">
          <span className="bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
            Centro de Control
          </span>
          <span className="text-xs px-3 py-1 bg-cyan-900/30 text-cyan-300 border border-cyan-500/20 rounded-full font-normal">
            {teams.reduce((acc, t) => acc + t.agents.length, 0)} agentes activos
          </span>
        </h2>
        <p className="text-gray-400 mt-1">Supervisá el estado de los agentes, herramientas y módulos del ecosistema.</p>
      </div>

      {/* Agentes */}
      <div>
        <h3 className="text-xl font-bold text-gray-200 mb-4 flex items-center gap-2">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
          Agentes en línea
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teams.flatMap(team => team.agents).map(agent => (
            <div
              key={agent.name}
              className="bg-gray-800/60 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-5 flex flex-col gap-4 transition-all duration-300 hover:border-cyan-500/40 hover:shadow-lg hover:shadow-cyan-500/5 group"
            >
              <div className="flex items-center gap-4">
                <div className="relative">
                  <div className="text-4xl">{agent.emoji}</div>
                  <span className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-gray-800 ${
                    agent.status === 'working' ? 'bg-yellow-400 animate-pulse' :
                    agent.status === 'done' ? 'bg-green-400' :
                    agent.status === 'error' ? 'bg-red-400' : 'bg-gray-600'
                  }`}></span>
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-bold text-gray-200 group-hover:text-cyan-300 transition-colors truncate">{agent.name}</h4>
                  <p className="text-xs text-gray-400 truncate">{agent.role}</p>
                  {agent.current_task && (
                    <p className="text-xs text-cyan-400 mt-1 truncate italic">"{agent.current_task}"</p>
                  )}
                </div>
              </div>
              {agent.tools && agent.tools.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {agent.tools.map(tool => (
                    <span
                      key={tool}
                      className="text-xs bg-gray-700/50 text-gray-300 px-2 py-0.5 rounded-full border border-gray-600/50"
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              )}
              <div className="text-xs text-gray-500 mt-auto">
                {agent.status === 'working' ? '⏳ Trabajando...' :
                 agent.status === 'done' ? '✅ Disponible' :
                 agent.status === 'error' ? '❌ Falló' : '⚪ En espera'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Herramientas y Módulos (secciones colapsables) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Herramientas */}
        <div>
          <button
            onClick={() => toggleSection('tools')}
            className="w-full flex items-center justify-between text-left mb-3 group"
          >
            <h3 className="text-xl font-bold text-gray-200 flex items-center gap-2">
              <span className="text-cyan-400">🛠️</span> Herramientas
              <span className="text-xs text-gray-500 font-normal">({tools.length})</span>
            </h3>
            <span className={`text-gray-400 transform transition-transform duration-200 ${expandedSections.tools ? 'rotate-180' : ''}`}>
              ▼
            </span>
          </button>
          <div className={`grid grid-cols-1 gap-2 transition-all duration-300 ${expandedSections.tools ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
            {tools.map(tool => (
              <div key={tool.name} className="bg-gray-800/40 border border-gray-700/30 rounded-xl p-3 flex items-center gap-3 hover:border-cyan-500/30 transition-all">
                <span className="text-cyan-400 text-lg">🔧</span>
                <div>
                  <h4 className="text-sm font-medium text-gray-300">{tool.name}</h4>
                  <p className="text-xs text-gray-500">{tool.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Módulos Core */}
        <div>
          <button
            onClick={() => toggleSection('core')}
            className="w-full flex items-center justify-between text-left mb-3 group"
          >
            <h3 className="text-xl font-bold text-gray-200 flex items-center gap-2">
              <span className="text-purple-400">⚙️</span> Módulos Core
              <span className="text-xs text-gray-500 font-normal">({coreModules.length})</span>
            </h3>
            <span className={`text-gray-400 transform transition-transform duration-200 ${expandedSections.core ? 'rotate-180' : ''}`}>
              ▼
            </span>
          </button>
          <div className={`grid grid-cols-1 gap-2 transition-all duration-300 ${expandedSections.core ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
            {coreModules.map(mod => (
              <div key={mod.name} className="bg-gray-800/40 border border-gray-700/30 rounded-xl p-3 flex items-center gap-3 hover:border-purple-500/30 transition-all">
                <span className="text-purple-400 text-lg">⚙️</span>
                <div>
                  <h4 className="text-sm font-medium text-gray-300 font-mono">{mod.name}</h4>
                  <p className="text-xs text-gray-500">{mod.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}