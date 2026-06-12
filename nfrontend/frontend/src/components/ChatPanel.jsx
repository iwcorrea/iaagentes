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

const AGENT_TASKS = {
  'Director IA': 'Planificando arquitectura...',
  'Code Generator': 'Escribiendo backend...',
  'Frontend Designer': 'Diseñando interfaz...',
  'QA Auditor': 'Auditando código...',
  'Repair Agent': 'Reparando errores...',
  'Dependency Manager': 'Gestionando dependencias...'
}

export default function ChatPanel() {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [scope, setScope] = useState('all')
  const [mode, setMode] = useState('full')
  const [turbo, setTurbo] = useState(false)
  const [showGuided, setShowGuided] = useState(false)
  const [agentStatus, setAgentStatus] = useState({})
  const [progressMessages, setProgressMessages] = useState([])
  const { activeProjectId, projectName, setActiveProjectId, chatMessages, setChatMessages } = useProject()
  const bottomRef = useRef(null)
  const { showToast, ToastContainer } = useToast()

  // Polling del estado de los agentes
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
          setAgentStatus(prev => {
            if (JSON.stringify(prev) === JSON.stringify(statusMap)) return prev
            const msgs = []
            Object.entries(statusMap).forEach(([name, status]) => {
              if (status === 'working') {
                msgs.push(`${AGENT_EMOJIS[name] || '🤖'} ${name}: ${AGENT_TASKS[name] || 'Trabajando...'}`)
              } else if (status === 'done') {
                msgs.push(`${AGENT_EMOJIS[name] || '🤖'} ${name}: ✅ Completado`)
              } else if (status === 'error') {
                msgs.push(`${AGENT_EMOJIS[name] || '🤖'} ${name}: ❌ Error`)
              }
            })
            setProgressMessages(msgs)
            return statusMap
          })
        } catch {}
      }, 2000)
    } else {
      setAgentStatus({})
      setProgressMessages([])
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
      const params = { turbo }
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
      if (activeProjectId) {
        api.post(`/projects/${activeProjectId}/chat`, { messages: finalMessages })
      }
    } catch (err) {
      showToast('Error al comunicarse con los agentes', 'error')
      setChatMessages(prev => [...prev, { role: 'assistant', content: '❌ Error de conexión' }])
    } finally {
      setLoading(false)
    }
  }, [input, loading, chatMessages, activeProjectId, scope, mode, turbo, showToast, setActiveProjectId, setChatMessages])

  const placeholderText = activeProjectId
    ? `Modificar "${projectName || activeProjectId}"...`
    : 'Crear un nuevo proyecto...'

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {chatMessages.length === 0 && !loading && (
          <div className="text-center text-gray-500 mt-20">
            <div className="text-6xl mb-4">🧠</div>
            <p className="text-xl font-semibold text-gray-300">¿Qué proyecto querés crear, parce?</p>
            <p className="text-sm text-gray-500 mt-2">
              Describí la aplicación o usá el{' '}
              <span className="text-purple-400 cursor-pointer underline" onClick={() => setShowGuided(true)}>
                Proyecto Guiado
              </span>
            </p>
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
            <div className="bg-gray-800/80 border border-gray-700/50 px-5 py-3 rounded-2xl text-sm text-gray-300 max-w-[80%]">
              <div className="flex items-center gap-2 mb-3">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                <span className="font-medium">Los agentes están trabajando...</span>
              </div>
              {progressMessages.length > 0 && (
                <div className="space-y-1.5">
                  {progressMessages.map((msg, i) => (
                    <div key={i} className="text-xs text-gray-400 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                      {msg}
                    </div>
                  ))}
                </div>
              )}
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
      {showGuided && <GuidedProjectCreator onClose={() => setShowGuided(false)} onProjectCreated={id => { setActiveProjectId(id); setShowGuided(false); }} />}
      <ToastContainer />
    </div>
  )
}