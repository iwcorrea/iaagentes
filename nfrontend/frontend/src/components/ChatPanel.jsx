import { useState, useRef, useEffect, useCallback } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'
import { useToast } from '../hooks/useToast'

export default function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const { activeProjectId } = useProject()
  const bottomRef = useRef(null)
  const { showToast } = useToast()

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

  return (
    <div className="flex flex-col h-full p-4">
      <div className="flex-1 overflow-y-auto space-y-3 mb-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 dark:text-gray-500 mt-20">
            <p className="text-lg font-medium">¿Qué proyecto querés crear, parce?</p>
            <p className="text-sm">Describí la aplicación y los agentes se pondrán a trabajar.</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] px-4 py-2 rounded-2xl text-sm ${
              m.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }`}>
              <pre className="whitespace-pre-wrap font-sans">{m.content}</pre>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-2xl text-sm animate-pulse">
              Los agentes están trabajando...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
          className="flex-1 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none"
          placeholder="Describí la aplicación que necesitás..."
        />
        <button onClick={send} disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-3 rounded-xl font-medium transition disabled:opacity-50">
          Enviar
        </button>
      </div>
    </div>
  )
}