import { useState, useRef, useEffect, useCallback } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'
import { useToast } from '../hooks/useToast'

export default function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
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
      const res = await api.post('/v1/chat/completions', {
        messages: [...messages, userMsg]
      }, {
        params: activeProjectId ? { project_id: activeProjectId } : {}
      })
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
  }, [input, loading, messages, activeProjectId, showToast])

  const placeholderText = activeProjectId
    ? `Modificar "${projectName || activeProjectId}"...`
    : 'Crear un nuevo proyecto...'

  const buttonText = activeProjectId ? 'Modificar' : 'Crear'

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            <div className="text-6xl mb-4">🧠</div>
            <p className="text-xl font-semibold text-gray-300">
              {activeProjectId
                ? `Modificando "${projectName || activeProjectId}"`
                : '¿Qué proyecto querés crear, parce?'}
            </p>
            <p className="text-sm text-gray-500">
              {activeProjectId
                ? 'Escribí los cambios que necesitás.'
                : 'Describí la aplicación y los agentes se pondrán a trabajar.'}
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
            <div className="bg-gray-800/80 border border-gray-700/50 px-5 py-3 rounded-2xl text-sm animate-pulse text-gray-400">
              Los agentes están trabajando...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="p-4 border-t border-gray-700/30 bg-gray-800/30">
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
            {buttonText}
          </button>
        </div>
      </div>
      <ToastContainer />
    </div>
  )
}