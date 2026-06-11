import { useState, useEffect } from 'react'
import api from '../api/axios'

const statusEmojis = {
  idle: '🟢',
  working: '🟡',
  error: '🔴'
}

export default function TeamPanel() {
  const [agents, setAgents] = useState([])
  const [tools, setTools] = useState([])
  const [coreModules, setCoreModules] = useState([])

  useEffect(() => {
    api.get('/api/agents')
      .then(res => {
        setAgents(res.data.agents || [])
        setTools(res.data.tools || [])
        setCoreModules(res.data.core_modules || [])
      })
      .catch(console.error)
  }, [])

  return (
    <div className="p-6 space-y-8">
      {/* Sección de agentes */}
      <div>
        <h2 className="text-2xl font-bold text-gray-100 mb-4">🧑‍💼 Nuestro Equipo</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map(agent => (
            <div key={agent.name} className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-5 flex flex-col gap-3 hover:border-blue-500/30 transition-all shadow-lg">
              <div className="flex items-center gap-3">
                <div className="text-4xl">{agent.emoji}</div>
                <div>
                  <h3 className="font-bold text-gray-200">{agent.name}</h3>
                  <p className="text-xs text-gray-400">{agent.role}</p>
                </div>
                <span className="ml-auto text-lg" title={agent.status}>{statusEmojis[agent.status] || '🟢'}</span>
              </div>
              <p className="text-sm text-gray-500">{agent.description}</p>
              <div className="flex flex-wrap gap-1">
                {agent.tools.map(tool => (
                  <span key={tool} className="text-xs bg-blue-900/30 text-blue-300 px-2 py-0.5 rounded-full border border-blue-500/20">
                    🔧 {tool}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sección de herramientas */}
      <div>
        <h2 className="text-2xl font-bold text-gray-100 mb-4">🛠️ Herramientas</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {tools.map(tool => (
            <div key={tool.name} className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-4 flex items-center gap-3 hover:border-green-500/30 transition-all">
              <span className="text-2xl">🔧</span>
              <div>
                <h4 className="font-medium text-gray-200">{tool.name}</h4>
                <p className="text-xs text-gray-500">{tool.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sección de core */}
      <div>
        <h2 className="text-2xl font-bold text-gray-100 mb-4">⚙️ Módulos Core</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {coreModules.map(mod => (
            <div key={mod.name} className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl p-4 flex items-center gap-3 hover:border-purple-500/30 transition-all">
              <span className="text-2xl">⚙️</span>
              <div>
                <h4 className="font-medium text-gray-200 font-mono text-sm">{mod.name}</h4>
                <p className="text-xs text-gray-500">{mod.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}