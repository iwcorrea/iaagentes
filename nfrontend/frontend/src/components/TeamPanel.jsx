import { useState, useEffect, useCallback } from 'react'
import api from '../api/axios'

const statusEmojis = {
  idle: '🟢',
  working: '🟡',
  error: '🔴'
}

export default function TeamPanel() {
  const [teams, setTeams] = useState([])
  const [tools, setTools] = useState([])
  const [coreModules, setCoreModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedTeams, setExpandedTeams] = useState({})
  const [expandedSections, setExpandedSections] = useState({ tools: true, core: true })

  const toggleTeam = (teamName) => {
    setExpandedTeams(prev => ({ ...prev, [teamName]: !prev[teamName] }))
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const loadData = useCallback(async () => {
    try {
      const res = await api.get('/api/agents')
      setTeams(res.data.teams || [])
      setTools(res.data.tools || [])
      setCoreModules(res.data.core_modules || [])
      // Inicializar todos los equipos expandidos
      const expanded = {}
      ;(res.data.teams || []).forEach(t => { expanded[t.name] = true })
      setExpandedTeams(expanded)
    } catch (err) {
      console.error('Error al cargar datos:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadData() }, [loadData])
  useEffect(() => {
    const interval = setInterval(loadData, 10000)
    return () => clearInterval(interval)
  }, [loadData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
        <span className="ml-3 text-gray-400">Cargando equipos...</span>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Sección de equipos con acordeón */}
      <div>
        <h2 className="text-2xl font-bold text-gray-100 mb-4">👥 Equipos</h2>
        {teams.map(team => (
          <div key={team.name} className="mb-4 bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl overflow-hidden">
            <button
              onClick={() => toggleTeam(team.name)}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30 transition"
            >
              <div>
                <h3 className="text-lg font-bold text-gray-200">{team.name}</h3>
                <p className="text-xs text-gray-400">{team.description}</p>
              </div>
              <span className="text-gray-400 transform transition-transform duration-200" style={{ transform: expandedTeams[team.name] ? 'rotate(180deg)' : 'rotate(0deg)' }}>
                ▼
              </span>
            </button>
            {expandedTeams[team.name] && (
              <div className="p-4 pt-0">
                {team.agents.length === 0 ? (
                  <p className="text-gray-500 text-sm py-4">No hay agentes asignados a este equipo.</p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {team.agents.map(agent => (
                      <div key={agent.name} className="bg-gray-800 border border-gray-600/50 rounded-xl p-3 flex items-center gap-3 hover:border-blue-500/30 transition-all">
                        <span className="text-2xl">{agent.emoji}</span>
                        <div className="min-w-0 flex-1">
                          <h4 className="font-medium text-gray-200 text-sm truncate">{agent.name}</h4>
                          <p className="text-xs text-gray-500 truncate">{agent.role}</p>
                          {agent.tools.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {agent.tools.map(tool => (
                                <span key={tool} className="text-xs bg-blue-900/30 text-blue-300 px-1.5 py-0.5 rounded-full border border-blue-500/20">
                                  {tool}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <span title={agent.status}>{statusEmojis[agent.status] || '🟢'}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Sección de herramientas */}
      <div>
        <button
          onClick={() => toggleSection('tools')}
          className="w-full flex items-center justify-between mb-4"
        >
          <h2 className="text-2xl font-bold text-gray-100">🛠️ Herramientas</h2>
          <span className="text-gray-400 transform transition-transform duration-200" style={{ transform: expandedSections.tools ? 'rotate(180deg)' : 'rotate(0deg)' }}>▼</span>
        </button>
        {expandedSections.tools && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {tools.length === 0 ? (
              <p className="text-gray-500 col-span-full">No se encontraron herramientas.</p>
            ) : tools.map(tool => (
              <div key={tool.name} className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-3 hover:border-green-500/30 transition-all">
                <h4 className="font-medium text-gray-200 text-sm">{tool.name}</h4>
                <p className="text-xs text-gray-500 mt-1">{tool.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sección de módulos core */}
      <div>
        <button
          onClick={() => toggleSection('core')}
          className="w-full flex items-center justify-between mb-4"
        >
          <h2 className="text-2xl font-bold text-gray-100">⚙️ Módulos del sistema</h2>
          <span className="text-gray-400 transform transition-transform duration-200" style={{ transform: expandedSections.core ? 'rotate(180deg)' : 'rotate(0deg)' }}>▼</span>
        </button>
        {expandedSections.core && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {coreModules.length === 0 ? (
              <p className="text-gray-500 col-span-full">No se encontraron módulos.</p>
            ) : coreModules.map(mod => (
              <div key={mod.name} className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-3 hover:border-purple-500/30 transition-all">
                <h4 className="font-medium text-gray-200 text-sm font-mono">{mod.name}</h4>
                <p className="text-xs text-gray-500 mt-1">{mod.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}