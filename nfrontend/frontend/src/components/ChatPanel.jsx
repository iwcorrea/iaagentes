import { useState, useRef, useEffect } from 'react'
import api from '../api/axios'
import { useToast } from '../hooks/useToast'

export default function ChatPanel({ projectId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState('')
  const bottomRef = useRef(null)
  const { showToast } = useToast()

  // Cargar historial del chat al abrir un proyecto
  useEffect(() => {
    if (projectId) {
      api.get(`/projects/${projectId}/chat`)
        .then(res => setMessages(res.data.messages || []))
        .catch(() => setMessages([]))
    } else {
      setMessages([])
    }
  }, [projectId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setLoading(true)
    setProgress('Planificando arquitectura...')

    const userMsg = { role: 'user', content: text }
    const updated = [...messages, userMsg]
    setMessages(updated)

    try {
      const res = await api.post('/v1/chat/completions', {
        messages: updated
      }, {
        params: projectId ? { project_id: projectId } : {}
      })

      const reply = res.data.choices?.[0]?.message?.content || 'Sin respuesta'
      const assistantMsg = { role: 'assistant', content: reply }
      setMessages(prev => [...prev, assistantMsg])

      // Guardar historial
      if (projectId) {
        api.post(`/projects/${projectId}/chat`, {
          messages: [...updated, assistantMsg]
        })
      }
    } catch (err) {
      showToast('Error al comunicarse con los agentes', 'error')
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Error de conexión' }])
    } finally {
      setLoading(false)
      setProgress('')
    }
  }

  return (
    <div className="flex-1 flex flex-col p-4 md:p-6 overflow-hidden">
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex-1 overflow-y-auto mb-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 dark:text-gray-500 mt-20">
            <p className="text-lg font-medium">¿Qué proyecto querés crear, parce?</p>
            <p className="text-sm mt-2">Describí la aplicación y los agentes se pondrán a trabajar.</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`mb-3 ${m.role === 'user' ? 'text-right' : 'text-left'}`}>
            <span className={`inline-block max-w-2xl px-4 py-2 rounded-lg ${
              m.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
            }`}>
              <pre className="whitespace-pre-wrap text-sm font-sans">{m.content}</pre>
            </span>
          </div>
        ))}
        {loading && (
          <div className="text-center text-blue-600 dark:text-blue-400 text-sm mb-3">
            ⏳ {progress}
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-3">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
          rows={2}
          className="flex-1 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 resize-none focus:ring-2 focus:ring-blue-500 outline-none"
          placeholder="Describí la aplicación que necesitás..."
        />
        <button onClick={send} disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition self-end disabled:opacity-50">
          Enviar
        </button>
      </div>
    </div>
  )
}