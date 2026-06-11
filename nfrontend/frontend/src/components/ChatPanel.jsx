import { useState, useRef, useEffect, useCallback } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'
import { useToast } from '../hooks/useToast'

export default function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [scope, setScope] = useState('all')
  const [mode, setMode] = useState('full')
  const { activeProjectId, projectName } = useProject()
  const bottomRef = useRef(null)
  const { showToast, ToastContainer } = useToast()

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

      const res = await api.post('/v1/chat/completions', {
        messages: [...messages, userMsg]
      }, { params })

      const reply = res.data.choices?.[0]?.message?.content || 'Sin respuesta'
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])

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
  }, [input, loading, messages, activeProjectId, scope, mode, showToast])

  const placeholderText = activeProjectId
    ? `Modificar "${projectName || activeProjectId}"...`
    : 'Crear un nuevo proyecto...'

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {/* Mensajes... (sin cambios) */}
      </div>
      <div className="p-4 border-t border-gray-700/30 bg-gray-800/30">
        {/* Controles de ámbito y modo (solo si hay proyecto activo) */}
        {activeProjectId && (
          <div className="flex gap-3 mb-3">
            <select
              value={scope}
              onChange={e => setScope(e.target.value)}
              className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200"
            >
              <option value="all">Todo el proyecto</option>
              <option value="backend">Solo Backend</option>
              <option value="frontend">Solo Frontend</option>
            </select>
            <select
              value={mode}
              onChange={e => setMode(e.target.value)}
              className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200"
            >
              <option value="full">Contexto completo</option>
              <option value="light">Solo estructura</option>
            </select>
          </div>
        )}
        <div className="flex gap-3">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
            className="flex-1 bg-gray-800 border border-gray-600 rounded-xl px-5 py-3 text-sm text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-blue-500/50 outline-none transition"
            placeholder={placeholderText}
          />
          <button onClick={send} disabled={loading}
            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white px-6 py-3 rounded-xl font-semibold transition shadow-lg shadow-blue-500/20 disabled:opacity-50">
            {activeProjectId ? 'Modificar' : 'Crear'}
          </button>
        </div>
      </div>
      <ToastContainer />
    </div>
  )
}