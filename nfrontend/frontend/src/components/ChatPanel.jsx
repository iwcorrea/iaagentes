import { useState, useRef, useEffect, useCallback } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'

const PHASES = [
  { progress: 5, agent: 'Director IA', task: 'Analizando prompt...' },
  { progress: 20, agent: 'Director IA', task: 'Planificando arquitectura...' },
  { progress: 40, agent: 'Code Generator', task: 'Generando backend...' },
  { progress: 60, agent: 'Frontend Designer', task: 'Diseñando interfaz...' },
  { progress: 80, agent: 'QA Auditor', task: 'Revisando código...' },
  { progress: 95, agent: 'Sistema', task: 'Aplicando mejoras finales...' },
  { progress: 100, agent: 'Sistema', task: '¡Proyecto completado!' },
]

export default function ChatPanel() {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [scope, setScope] = useState('all')
  const [mode, setMode] = useState('full')
  const [turbo, setTurbo] = useState(false)
  const [brainModel, setBrainModel] = useState('cloud-coder')
  const [currentPhase, setCurrentPhase] = useState(null)
  const [progressMessages, setProgressMessages] = useState([])
  const [agentProgress, setAgentProgress] = useState(0)
  const [connectionStatus, setConnectionStatus] = useState('checking')
  const [toasts, setToasts] = useState([])
  const { activeProjectId, projectName, setActiveProjectId, chatMessages, setChatMessages } = useProject()
  const bottomRef = useRef(null)

  const showToast = useCallback((message, type = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])

  // Verificar estado de conexión
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const res = await api.get('/')
        if (res.data.status === 'ok') {
          try {
            await api.get('/api/agents')
            setConnectionStatus('connected')
          } catch {
            setConnectionStatus('limited')
          }
        }
      } catch {
        setConnectionStatus('disconnected')
      }
    }
    checkConnection()
    const interval = setInterval(checkConnection, 30000)
    return () => clearInterval(interval)
  }, [])

  // Polling del progreso
  useEffect(() => {
    let interval
    if (loading) {
      interval = setInterval(async () => {
        try {
          const res = await api.get('/api/agents')
          const progress = res.data.progress || 0
          setAgentProgress(progress)

          const phase = PHASES.find(p => progress <= p.progress) || PHASES[PHASES.length - 1]
          setCurrentPhase(phase)

          const msgs = []
          const teams = res.data.teams || []
          const allAgents = teams.flatMap(t => t.agents)
          allAgents.forEach(a => {
            if (a.status === 'working') {
              msgs.push(`${a.emoji} ${a.name}: ${a.current_task || 'Trabajando...'}`)
            } else if (a.status === 'done') {
              msgs.push(`${a.emoji} ${a.name}: ✅ Completado`)
            } else if (a.status === 'error') {
              msgs.push(`${a.emoji} ${a.name}: ❌ Error`)
            }
          })
          setProgressMessages(msgs)
        } catch {}
      }, 2000)
    } else {
      setCurrentPhase(null)
      setProgressMessages([])
      setAgentProgress(0)
    }
    return () => clearInterval(interval)
  }, [loading])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages, progressMessages])

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setLoading(true)

    const userMsg = { role: 'user', content: text }
    const updatedMessages = [...chatMessages, userMsg]
    setChatMessages(updatedMessages)

    try {
      const params = { turbo, brain_model: brainModel }
      if (activeProjectId) {
        params.project_id = activeProjectId
        params.scope = scope
        params.mode = mode
      }
      const res = await api.post('/v1/chat/completions', { messages: updatedMessages }, { params })
      const reply = res.data.choices?.[0]?.message?.content || 'Sin respuesta'
      const finalMessages = [...updatedMessages, { role: 'assistant', content: reply }]
      setChatMessages(finalMessages)

      const projectIdMatch = reply.match(/Proyecto ID: (\w+)/)
      if (projectIdMatch && !activeProjectId) {
        setActiveProjectId(projectIdMatch[1])
        showToast('¡Proyecto creado!', 'success')
      }
      // CORRECCIÓN: ruta con prefijo /api
      if (activeProjectId) {
        api.post(`/api/projects/${activeProjectId}/chat`, { messages: finalMessages }).catch(() => {})
      }
    } catch (err) {
      showToast('Error al comunicarse con los agentes', 'error')
      setChatMessages(prev => [...prev, { role: 'assistant', content: '❌ Error de conexión' }])
    } finally {
      setLoading(false)
    }
  }, [input, loading, chatMessages, activeProjectId, scope, mode, turbo, brainModel, setActiveProjectId, setChatMessages, showToast])

  const placeholderText = activeProjectId
    ? `Modificar "${projectName || activeProjectId}"...`
    : 'Crear un nuevo proyecto...'

  return (
    <div className="flex flex-col h-full relative">
      {/* Barra de estado de conexión */}
      <div className={`px-4 py-1 text-xs text-center ${
        connectionStatus === 'connected' ? 'bg-green-900/50 text-green-400' :
        connectionStatus === 'limited' ? 'bg-yellow-900/50 text-yellow-400' :
        'bg-red-900/50 text-red-400'
      }`}>
        {connectionStatus === 'connected' && '🟢 Sistema conectado'}
        {connectionStatus === 'limited' && '🟡 OpenRouter con rate‑limit'}
        {connectionStatus === 'disconnected' && '🔴 Sin conexión al servidor'}
      </div>

      {/* Toasts */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map(t => (
          <div key={t.id} className={`px-4 py-2 rounded-lg text-white text-sm shadow-lg transition-all ${
            t.type === 'error' ? 'bg-red-500' : t.type === 'success' ? 'bg-green-500' : 'bg-blue-500'
          }`}>
            {t.message}
          </div>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {chatMessages.length === 0 && !loading && (
          <div className="text-center text-gray-500 mt-20">
            <div className="text-6xl mb-4">🧠</div>
            <p className="text-xl font-semibold text-gray-300">¿Qué proyecto querés crear, parce?</p>
            <p className="text-sm text-gray-500 mt-2">Describí la aplicación y los agentes se pondrán a trabajar.</p>
          </div>
        )}
        {chatMessages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[75%] px-5 py-3 rounded-2xl text-sm ${
              m.role === 'user'
                ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white'
                : 'bg-gray-800/80 text-gray-100 border border-gray-700/50'
            }`}>
              <pre className="whitespace-pre-wrap font-sans">{m.content}</pre>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800/80 border border-gray-700/50 px-5 py-3 rounded-2xl text-sm text-gray-300 max-w-[80%] w-full">
              <div className="flex items-center gap-2 mb-3">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                <span className="font-medium">
                  {currentPhase ? currentPhase.task : 'Los agentes están trabajando...'}
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2 mb-3">
                <div
                  className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full transition-all duration-1000"
                  style={{ width: `${agentProgress}%` }}
                ></div>
              </div>
              <div className="space-y-1.5">
                {progressMessages.map((msg, i) => (
                  <div key={i} className="text-xs text-gray-400 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                    {msg}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="p-4 border-t border-gray-700/30 bg-gray-800/30">
        <div className="flex gap-3 mb-3">
          {activeProjectId && (
            <>
              <select value={scope} onChange={e => setScope(e.target.value)} className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200">
                <option value="all">Todo</option>
                <option value="backend">Backend</option>
                <option value="frontend">Frontend</option>
              </select>
              <select value={mode} onChange={e => setMode(e.target.value)} className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200">
                <option value="full">Completo</option>
                <option value="light">Ligero</option>
              </select>
            </>
          )}
          <select
            value={brainModel}
            onChange={e => setBrainModel(e.target.value)}
            className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200"
            title="Cerebro de los agentes"
          >
            <option value="local-coder">🦙 Local (Qwen 1.5B)</option>
            <option value="cloud-coder">☁️ Nube (OpenRouter)</option>
            <option value="hibrido-coder">🔀 Híbrido (Local + Nube)</option>
          </select>
          <label className="flex items-center gap-2 text-xs text-gray-400">
            <input type="checkbox" checked={turbo} onChange={e => setTurbo(e.target.checked)} />
            ⚡ Turbo
          </label>
        </div>
        <div className="flex gap-3">
          <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
            className="flex-1 bg-gray-800 border border-gray-600 rounded-xl px-5 py-3 text-sm text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-blue-500/50 outline-none"
            placeholder={placeholderText} />
          <button onClick={send} disabled={loading}
            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white px-6 py-3 rounded-xl font-semibold transition disabled:opacity-50">
            {activeProjectId ? 'Modificar' : 'Crear'}
          </button>
        </div>
      </div>
    </div>
  )
}