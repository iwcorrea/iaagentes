import { useState, useEffect, useCallback } from 'react'
import api from '../api/axios'

// ─── Secciones del panel ───
const SECTIONS = [
  { id: 'models', label: '🤖 Modelos', icon: '🤖' },
  { id: 'agents', label: '👤 Agentes', icon: '👤' },
  { id: 'teams', label: '👥 Equipos', icon: '👥' }
]

// ─── Componente principal ───
export default function SettingsPanel() {
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeSection, setActiveSection] = useState('models')
  const [toast, setToast] = useState(null)

  const showToast = (message, type = 'info') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  // Cargar configuración del backend
  const loadSettings = useCallback(async () => {
    try {
      const res = await api.get('/api/settings')
      setSettings(res.data)
    } catch (err) {
      showToast('Error al cargar configuración', 'error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadSettings() }, [loadSettings])

  // Persistencia local: tema y modelo preferido
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) document.documentElement.classList.toggle('dark', savedTheme === 'dark')
    const savedModel = localStorage.getItem('brainModel')
    if (savedModel && settings) {
      setSettings(prev => ({ ...prev, models: { ...prev.models, primary: savedModel } }))
    }
  }, [settings])

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.put('/api/settings', {
        models: settings.models,
        agents: settings.agents,
        teams: settings.teams
      })
      localStorage.setItem('brainModel', settings.models?.primary || 'gratuito-fallback')
      showToast('Configuración guardada', 'success')
    } catch (err) {
      showToast('Error al guardar', 'error')
    } finally {
      setSaving(false)
    }
  }

  // Handlers para modelos
  const updateModel = (field, value) => {
    setSettings(prev => ({ ...prev, models: { ...prev.models, [field]: value } }))
    if (field === 'primary') localStorage.setItem('brainModel', value)
  }

  // Handlers para agentes
  const toggleAgent = (name) => {
    setSettings(prev => {
      const agents = { ...prev.agents }
      if (agents[name]) agents[name] = { ...agents[name], enabled: !agents[name].enabled }
      return { ...prev, agents }
    })
  }

  const updateAgentBackstory = (name, backstory) => {
    setSettings(prev => {
      const agents = { ...prev.agents }
      if (agents[name]) agents[name] = { ...agents[name], backstory }
      return { ...prev, agents }
    })
  }

  // Handlers para equipos
  const addTeam = () => {
    const name = prompt('Nombre del nuevo equipo:')
    if (name?.trim()) {
      setSettings(prev => ({
        ...prev,
        teams: [...(prev.teams || []), { name: name.trim(), description: '', agents: [] }]
      }))
    }
  }

  const removeTeam = (index) => {
    setSettings(prev => ({ ...prev, teams: prev.teams.filter((_, i) => i !== index) }))
  }

  const toggleAgentInTeam = (teamIndex, agentName) => {
    setSettings(prev => {
      const teams = [...prev.teams]
      const team = { ...teams[teamIndex] }
      const agents = [...team.agents]
      team.agents = agents.includes(agentName) ? agents.filter(a => a !== agentName) : [...agents, agentName]
      teams[teamIndex] = team
      return { ...prev, teams }
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
        <span className="ml-3 text-gray-400">Cargando configuración...</span>
      </div>
    )
  }

  if (!settings) return <div className="p-6 text-gray-400">No se pudo cargar la configuración.</div>

  return (
    <div className="flex h-full">
      {/* Sidebar de secciones */}
      <aside className="w-56 bg-gray-800/40 border-r border-gray-700/30 p-4 space-y-2">
        <h2 className="text-lg font-bold text-gray-100 mb-4">⚙️ Configuración</h2>
        {SECTIONS.map(section => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`w-full text-left px-4 py-2 rounded-lg text-sm transition ${
              activeSection === section.id
                ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/30'
            }`}
          >
            {section.label}
          </button>
        ))}
        <div className="pt-4 border-t border-gray-700/30">
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-gradient-to-r from-green-600 to-emerald-500 text-white px-4 py-2 rounded-lg font-medium text-sm transition hover:from-green-500 disabled:opacity-50"
          >
            {saving ? 'Guardando...' : '💾 Guardar todo'}
          </button>
        </div>
      </aside>

      {/* Contenido dinámico */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeSection === 'models' && <ModelsSection settings={settings} updateModel={updateModel} />}
        {activeSection === 'agents' && (
          <AgentsSection
            agents={settings.available_agents || []}
            agentsConfig={settings.agents || {}}
            toggleAgent={toggleAgent}
            updateAgentBackstory={updateAgentBackstory}
          />
        )}
        {activeSection === 'teams' && (
          <TeamsSection
            teams={settings.teams || []}
            availableAgents={settings.available_agents || []}
            addTeam={addTeam}
            removeTeam={removeTeam}
            toggleAgentInTeam={toggleAgentInTeam}
          />
        )}
      </div>

      {/* Toast de notificación */}
      {toast && (
        <div className={`fixed bottom-4 right-4 z-50 px-4 py-2 rounded-lg text-white text-sm shadow-lg animate-slide-up ${
          toast.type === 'error' ? 'bg-red-500' : toast.type === 'success' ? 'bg-green-500' : 'bg-blue-500'
        }`}>
          {toast.message}
        </div>
      )}
    </div>
  )
}

// ─── Subcomponentes (factorizados) ───

function ModelsSection({ settings, updateModel }) {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-100">🤖 Modelos y LLM</h3>
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Modelo principal</label>
        <select
          value={settings.models?.primary || 'gratuito-fallback'}
          onChange={e => updateModel('primary', e.target.value)}
          className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-gray-200 w-full"
        >
          <option value="local-coder">🦙 Local (Qwen 1.5B)</option>
          <option value="cloud-coder">☁️ Nube (OpenRouter)</option>
          <option value="hibrido-coder">🔀 Híbrido</option>
        </select>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Temperatura</label>
          <input
            type="number" step="0.1" min="0" max="2"
            value={settings.models?.temperature ?? 0.0}
            onChange={e => updateModel('temperature', parseFloat(e.target.value))}
            className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-gray-200 w-full"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Max tokens</label>
          <input
            type="number" step="256" min="256" max="8192"
            value={settings.models?.max_tokens ?? 4096}
            onChange={e => updateModel('max_tokens', parseInt(e.target.value))}
            className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-gray-200 w-full"
          />
        </div>
      </div>
    </div>
  )
}

function AgentsSection({ agents, agentsConfig, toggleAgent, updateAgentBackstory }) {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-100">👤 Agentes</h3>
      {agents.map(agent => {
        const config = agentsConfig[agent.name] || { enabled: true, backstory: '', tools: [] }
        return (
          <div key={agent.name} className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{agent.emoji || '🤖'}</span>
                <div>
                  <h4 className="font-bold text-gray-200">{agent.name}</h4>
                  <p className="text-xs text-gray-400">{agent.role}</p>
                </div>
              </div>
              <button
                onClick={() => toggleAgent(agent.name)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition ${
                  config.enabled
                    ? 'bg-green-600/20 text-green-400 border border-green-500/30'
                    : 'bg-red-600/20 text-red-400 border border-red-500/30'
                }`}
              >
                {config.enabled ? 'Activado' : 'Desactivado'}
              </button>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Backstory</label>
              <textarea
                value={config.backstory || ''}
                onChange={e => updateAgentBackstory(agent.name, e.target.value)}
                rows={3}
                className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200 w-full resize-none"
              />
            </div>
            <div className="flex flex-wrap gap-1">
              {(config.tools || agent.tools || []).map(tool => (
                <span key={tool} className="text-xs bg-gray-700/50 text-gray-300 px-2 py-0.5 rounded-full border border-gray-600/50">
                  {tool}
                </span>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function TeamsSection({ teams, availableAgents, addTeam, removeTeam, toggleAgentInTeam }) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold text-gray-100">👥 Equipos</h3>
        <button onClick={addTeam} className="bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg text-sm transition">
          + Nuevo equipo
        </button>
      </div>
      {teams.map((team, idx) => (
        <div key={idx} className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-4 space-y-3">
          <div className="flex justify-between items-center">
            <h4 className="font-bold text-gray-200">{team.name}</h4>
            <button onClick={() => removeTeam(idx)} className="text-red-400 hover:text-red-300 text-sm">
              🗑️ Eliminar
            </button>
          </div>
          <p className="text-sm text-gray-400">{team.description || 'Sin descripción'}</p>
          <div>
            <h5 className="text-sm font-medium text-gray-300 mb-2">Agentes asignados</h5>
            <div className="grid grid-cols-2 gap-2">
              {availableAgents.map(agent => (
                <label key={agent.name} className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={(team.agents || []).includes(agent.name)}
                    onChange={() => toggleAgentInTeam(idx, agent.name)}
                    className="rounded bg-gray-700 border-gray-600"
                  />
                  {agent.emoji || '🤖'} {agent.name}
                </label>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}