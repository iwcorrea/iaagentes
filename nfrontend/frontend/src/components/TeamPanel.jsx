import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import api from '../api/axios'

/* ------------------------------------------------------------------ */
/*  Subcomponentes (extraídos para claridad y React.memo)             */
/* ------------------------------------------------------------------ */

const AgentCard = React.memo(({ agent }) => (
  <div className="bg-gray-800/60 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-5 flex flex-col gap-4 transition-all duration-300 hover:border-cyan-500/40 hover:shadow-lg hover:shadow-cyan-500/5 group">
    <div className="flex items-center gap-4">
      <div className="relative shrink-0">
        <div className="text-4xl">{agent.emoji}</div>
        <span className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-gray-800 ${
          agent.status === 'working' ? 'bg-yellow-400 animate-pulse' :
          agent.status === 'done' ? 'bg-green-400' :
          agent.status === 'error' ? 'bg-red-400' : 'bg-gray-600'
        }`} />
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
        {agent.tools.map((tool, idx) => (
          <span key={`${tool}-${idx}`} className="text-xs bg-gray-700/50 text-gray-300 px-2 py-0.5 rounded-full border border-gray-600/50">
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
))

const CollapsibleSection = React.memo(({ title, icon, count, expanded, onToggle, children }) => {
  const contentRef = useRef(null)
  const [height, setHeight] = useState(0)

  useEffect(() => {
    if (contentRef.current) {
      setHeight(expanded ? contentRef.current.scrollHeight : 0)
    }
  }, [expanded, children])

  return (
    <div>
      <button onClick={onToggle} className="w-full flex items-center justify-between text-left mb-3 group">
        <h3 className="text-xl font-bold text-gray-200 flex items-center gap-2">
          <span className={icon === 'tools' ? 'text-cyan-400' : 'text-purple-400'}>{icon === 'tools' ? '🛠️' : '⚙️'}</span>
          {title}
          <span className="text-xs text-gray-500 font-normal">({count})</span>
        </h3>
        <span className={`text-gray-400 transform transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}>▼</span>
      </button>
      <div
        ref={contentRef}
        className="overflow-hidden transition-all duration-300 ease-in-out"
        style={{ maxHeight: `${height}px` }}
      >
        <div className="grid grid-cols-1 gap-2 pb-2">
          {children}
        </div>
      </div>
    </div>
  )
})

const ItemRow = React.memo(({ item, icon }) => (
  <div className="bg-gray-800/40 border border-gray-700/30 rounded-xl p-3 flex items-center gap-3 hover:border-cyan-500/30 transition-all">
    <span className="text-lg">{icon}</span>
    <div>
      <h4 className="text-sm font-medium text-gray-300 font-mono">{item.name}</h4>
      <p className="text-xs text-gray-500">{item.description}</p>
    </div>
  </div>
))

/* ------------------------------------------------------------------ */
/*  Componente principal                                              */
/* ------------------------------------------------------------------ */

export default function TeamPanel() {
  const [teams, setTeams] = useState([])
  const [tools, setTools] = useState([])
  const [coreModules, setCoreModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedSections, setExpandedSections] = useState({ tools: false, core: false })

  const loadData = useCallback(async () => {
    try {
      const res = await api.get('/api/agents')
      setTeams(res.data.teams || [])
      setTools(res.data.tools || [])
      setCoreModules(res.data.core_modules || [])
      setError(null)
    } catch (err) {
      console.error('Error al cargar datos del equipo:', err)
      setError('No se pudieron cargar los datos del centro de control.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 10000)
    return () => clearInterval(interval)
  }, [loadData])

  const toggleSection = useCallback((section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }, [])

  const totalAgents = useMemo(() => teams.reduce((acc, t) => acc + t.agents.length, 0), [teams])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
        <span className="ml-3 text-gray-400">Cargando centro de control...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-64 text-center">
        <div className="text-4xl mb-3">⚠️</div>
        <p className="text-red-400">{error}</p>
        <button onClick={loadData} className="mt-4 px-4 py-2 bg-cyan-600/20 text-cyan-400 rounded-lg hover:bg-cyan-600/30 transition">
          Reintentar
        </button>
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
            {totalAgents} agentes activos
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
            <AgentCard key={agent.name} agent={agent} />
          ))}
        </div>
      </div>

      {/* Herramientas y Módulos (secciones colapsables) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CollapsibleSection
          title="Herramientas"
          icon="tools"
          count={tools.length}
          expanded={expandedSections.tools}
          onToggle={() => toggleSection('tools')}
        >
          {tools.map(tool => (
            <ItemRow key={tool.name} item={tool} icon="🔧" />
          ))}
        </CollapsibleSection>

        <CollapsibleSection
          title="Módulos Core"
          icon="core"
          count={coreModules.length}
          expanded={expandedSections.core}
          onToggle={() => toggleSection('core')}
        >
          {coreModules.map(mod => (
            <ItemRow key={mod.name} item={mod} icon="⚙️" />
          ))}
        </CollapsibleSection>
      </div>
    </div>
  )
}