import { useState, useEffect, useCallback } from 'react'
import api from '../api/axios'
import { useToast } from '../hooks/useToast'

export default function SettingsPanel() {
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeSection, setActiveSection] = useState('models')
  const { showToast } = useToast()

  const loadSettings = useCallback(async () => {
    try {
      const res = await api.get('/api/settings')
      setSettings(res.data)
    } catch (err) {
      showToast('Error al cargar configuración', 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => { loadSettings() }, [loadSettings])

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.put('/api/settings', {
        models: settings.models,
        agents: settings.agents,
        teams: settings.teams
      })
      showToast('Configuración guardada correctamente', 'success')
    } catch (err) {
      showToast('Error al guardar configuración', 'error')
    } finally {
      setSaving(false)
    }
  }

  const updateModel = (field, value) => {
    setSettings(prev => ({
      ...prev,
      models: { ...prev.models, [field]: value }
    }))
  }

  const toggleAgent = (name) => {
    setSettings(prev => {
      const agents = { ...prev.agents }
      if (agents[name]) {
        agents[name] = { ...agents[name], enabled: !agents[name].enabled }
      }
      return { ...prev, agents }
    })
  }

  const updateAgentBackstory = (name, backstory) => {
    setSettings(prev => {
      const agents = { ...prev.agents }
      if (agents[name]) {
        agents[name] = { ...agents[name], backstory }
      }
      return { ...prev, agents }
    })
  }

  const addTeam = () => {
    const name = prompt('Nombre del nuevo equipo:')
    if (name && name.trim()) {
      setSettings(prev => ({
        ...prev,
        teams: [...(prev.teams || []), { name: name.trim(), description: '', agents: [] }]
      }))
    }
  }

  const removeTeam = (index) => {
    setSettings(prev => ({
      ...prev,
      teams: prev.teams.filter((_, i) => i !== index)
    }))
  }

  const toggleAgentInTeam = (teamIndex, agentName) => {
    setSettings(prev => {
      const teams = [...prev.teams]
      const team = { ...teams[teamIndex] }
      const agents = [...team.agents]
      if (agents.includes(agentName)) {
        team.agents = agents.filter(a => a !== agentName)
      } else {
        team.agents = [...agents, agentName]
      }
      teams[teamIndex] = team
      return { ...prev, teams }
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
        <span className="ml-3 text-gray-400">Cargando configuración...</span>
      </div>
    )
  }

  if (!settings) return <div className="p-6 text-gray-400">No se pudo cargar la configuración.</div>

  return (
    <div className="flex h-full">
      {/* Sidebar de secciones */}
      <aside className="w-56 bg-gray-800/50 border-r border-gray-700/50 p-4 space-y-2">
        <h2 className="text-lg font-bold text-gray-100 mb-4">⚙️ Configuración</h2>
        {[
          { id: 'models', label: '🤖 Modelos', icon: '🤖' },
          { id: 'agents', label: '👤 Agentes', icon: '👤' },
          { id: 'teams', label: '👥 Equipos', icon: '👥' }
        ].map(section => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`w-full text-left px-4 py-2 rounded-lg text-sm transition ${
              activeSection === section.id
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/30'
            }`}
          >
            {section.label}
          </button>
        ))}
        <div className="pt-4 border-t border-gray-700/50">
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-gradient-to-r from-green-600 to-emerald-500 text-white px-4 py-2 rounded-lg font-medium text-sm transition hover:from-green-500 disabled:opacity-50"
          >
            {saving ? 'Guardando...' : '💾 Guardar todo'}
          </button>
        </div>
      </aside>

      {/* Contenido de la sección */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeSection === 'models' && (
          <div className="space-y-6">
            <h3 className="text-xl font-bold text-gray-100">🤖 Modelos y LLM</h3>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Modelo principal</label>
              <select
                value={settings.models?.primary || 'gratuito-fallback'}
                onChange={e => updateModel('primary', e.target.value)}
                className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-gray-200 w-full"
              >
                <option value="gratuito-fallback">gratuito-fallback (proxy LiteLLM)</option>
                <option value="openrouter/deepseek/deepseek-v4-flash:free">DeepSeek v4 Flash</option>
                <option value="openrouter/qwen/qwen3-coder:free">Qwen 3 Coder</option>
                <option value="openrouter/meta-llama/llama-3.3-70b-instruct:free">Llama 3.3 70B</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Temperatura</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={settings.models?.temperature ?? 0.0}
                  onChange={e => updateModel('temperature', parseFloat(e.target.value))}
                  className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-gray-200 w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Max tokens</label>
                <input
                  type="number"
                  step="256"
                  min="256"
                  max="8192"
                  value={settings.models?.max_tokens ?? 4096}
                  onChange={e => updateModel('max_tokens', parseInt(e.target.value))}
                  className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-gray-200 w-full"
                />
              </div>
            </div>
          </div>
        )}

        {activeSection === 'agents' && (
          <div className="space-y-6">
            <h3 className="text-xl font-bold text-gray-100">👤 Agentes</h3>
            {settings.available_agents?.map(agent => {
              const agentConfig = settings.agents?.[agent.name] || { enabled: true, backstory: '', tools: [] }
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
                        agentConfig.enabled
                          ? 'bg-green-600/20 text-green-400 border border-green-500/30'
                          : 'bg-red-600/20 text-red-400 border border-red-500/30'
                      }`}
                    >
                      {agentConfig.enabled ? 'Activado' : 'Desactivado'}
                    </button>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Backstory</label>
                    <textarea
                      value={agentConfig.backstory || ''}
                      onChange={e => updateAgentBackstory(agent.name, e.target.value)}
                      rows={3}
                      className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200 w-full resize-none"
                    />
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {(agentConfig.tools || agent.tools || []).map(tool => (
                      <span key={tool} className="text-xs bg-blue-900/30 text-blue-300 px-2 py-0.5 rounded-full border border-blue-500/20">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {activeSection === 'teams' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-100">👥 Equipos</h3>
              <button onClick={addTeam} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition">
                + Nuevo equipo
              </button>
            </div>
            {(settings.teams || []).map((team, idx) => (
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
                    {(settings.available_agents || []).map(agent => (
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
        )}
      </div>
    </div>
  )
}