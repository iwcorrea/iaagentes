import { useState, useRef, useEffect, useCallback } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'
import { useToast } from '../hooks/useToast'
import GuidedProjectCreator from './GuidedProjectCreator'

const AGENT_EMOJIS = {
  'Director IA': '🧠',
  'Code Generator': '💻',
  'Frontend Designer': '🎨',
  'QA Auditor': '🔍',
  'Repair Agent': '🔧',
  'Dependency Manager': '📦'
}

export default function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [scope, setScope] = useState('all')
  const [mode, setMode] = useState('full')
  const [showGuided, setShowGuided] = useState(false)
  const [agentStatus, setAgentStatus] = useState({})
  const { activeProjectId, projectName, setActiveProjectId } = useProject()
  const bottomRef = useRef(null)
  const { showToast, ToastContainer } = useToast()

  // Cargar estado de agentes cada 2 segundos mientras está cargando
  useEffect(() => {
    let interval
    if (loading) {
      interval = setInterval(async () => {
        try {
          const res = await api.get('/api/agents')
          const teams = res.data.teams || []
          const allAgents = teams.flatMap(t => t.agents)
          const statusMap = {}
          allAgents.forEach(a => { statusMap[a.name] = a.status })
          setAgentStatus(statusMap)
        } catch {}
      }, 2000)
    } else {
      setAgentStatus({})
    }
    return () => clearInterval(interval)
  }, [loading])

  useEffect(() => {
    if (activeProjectId) {
      api.get(`/projects/${activeProjectId}/chat`)
        .then(res => setMessages(res.data.messages || []))
        .catch(() => setMessages([]))
    } else {
      setMessages([])
    }
  }, [activeProjectId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setLoading(true)

    const userMsg = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])

    try {
      const params = {}
      if (activeProjectId) {
        params.project_id = activeProjectId
        params.scope = scope
        params.mode = mode
      }
      const res = await api.post('/v1/chat/completions', { messages: [...messages, userMsg] }, { params })
      const reply = res.data.choices?.[0]?.message?.content || 'Sin respuesta'
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])

      const projectIdMatch = reply.match(/Proyecto ID: (\w+)/)
      if (projectIdMatch && !activeProjectId) {
        setActiveProjectId(projectIdMatch[1])
        showToast('¡Proyecto creado con éxito!', 'success')
      }
      if (activeProjectId) {
        api.post(`/projects/${activeProjectId}/chat`, {
          messages: [...messages, userMsg, { role: 'assistant', content: reply }]
        })
      }
    } catch (err) {
      showToast('Error al comunicarse con los agentes', 'error')
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Error de conexión' }])
    } finally {
      setLoading(false)
    }
  }, [input, loading, messages, activeProjectId, scope, mode, showToast, setActiveProjectId])

  const placeholderText = activeProjectId
    ? `Modificar "${projectName || activeProjectId}"...`
    : 'Crear un nuevo proyecto...'

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.length === 0 && !loading && (
          <div className="text-center text-gray-500 mt-20">
            <div className="text-6xl mb-4">🧠</div>
            <p className="text-xl font-semibold text-gray-300">¿Qué proyecto querés crear, parce?</p>
            <p className="text-sm text-gray-500 mt-2">
              Describí la aplicación o usá el{' '}
              <span className="text-purple-400 font-semibold cursor-pointer underline hover:text-purple-300" onClick={() => setShowGuided(true)}>
                Proyecto Guiado
              </span>
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[75%] px-5 py-3 rounded-2xl text-sm shadow-lg ${
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
            <div className="bg-gray-800/80 border border-gray-700/50 px-5 py-3 rounded-2xl text-sm text-gray-300">
              <div className="flex items-center gap-2 mb-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                <span className="font-medium">Los agentes están trabajando...</span>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-2">
                {Object.entries(AGENT_EMOJIS).map(([name, emoji]) => {
                  const status = agentStatus[name] || 'idle'
                  return (
                    <div key={name} className="flex items-center gap-2 text-xs">
                      <span>{emoji}</span>
                      <span className="text-gray-400">{name}</span>
                      <span className={`ml-auto w-2 h-2 rounded-full ${
                        status === 'working' ? 'bg-yellow-400 animate-pulse' :
                        status === 'done' ? 'bg-green-400' :
                        status === 'error' ? 'bg-red-400' : 'bg-gray-600'
                      }`}></span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      {/* Controles de ámbito y modo + input (sin cambios) */}
      <div className="p-4 border-t border-gray-700/30 bg-gray-800/30">
        {activeProjectId && (
          <div className="flex gap-3 mb-3">
            <select value={scope} onChange={e => setScope(e.target.value)} className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200">
              <option value="all">Todo el proyecto</option>
              <option value="backend">Solo Backend</option>
              <option value="frontend">Solo Frontend</option>
            </select>
            <select value={mode} onChange={e => setMode(e.target.value)} className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200">
              <option value="full">Contexto completo</option>
              <option value="light">Solo estructura</option>
            </select>
          </div>
        )}
        <div className="flex gap-3">
          <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
            className="flex-1 bg-gray-800 border border-gray-600 rounded-xl px-5 py-3 text-sm text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-blue-500/50 outline-none transition"
            placeholder={placeholderText} />
          <button onClick={send} disabled={loading}
            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white px-6 py-3 rounded-xl font-semibold transition shadow-lg shadow-blue-500/20 disabled:opacity-50">
            {activeProjectId ? 'Modificar' : 'Crear'}
          </button>
        </div>
      </div>
      {showGuided && (
        <GuidedProjectCreator onClose={() => setShowGuided(false)} onProjectCreated={(projectId) => { setActiveProjectId(projectId); setShowGuided(false); }} />
      )}
      <ToastContainer />
    </div>
  )
}