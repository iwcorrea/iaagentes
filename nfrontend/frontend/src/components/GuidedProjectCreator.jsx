import { useState, useEffect } from 'react'
import api from '../api/axios'

export default function GuidedProjectCreator({ onClose, onProjectCreated }) {
  const [step, setStep] = useState(0)
  const [templates, setTemplates] = useState([])
  const [selectedTemplate, setSelectedTemplate] = useState('')
  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState({})
  const [previewPrompt, setPreviewPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    api.get('/api/guided-templates')
      .then(res => setTemplates(res.data.templates || []))
      .catch(() => setTemplates([]))
  }, [])

  const handleSelectTemplate = async (id) => {
    setSelectedTemplate(id)
    const res = await api.get(`/api/guided-questions/${id}`)
    setQuestions(res.data.questions || [])
    setAnswers({})
    setStep(1)
  }

  const handlePreview = async () => {
    setLoading(true)
    const res = await api.post('/api/guided-preview', { template_id: selectedTemplate, answers })
    setPreviewPrompt(res.data.prompt)
    setStep(2)
    setLoading(false)
  }

  const handleCreate = async () => {
    setLoading(true)
    const res = await api.post('/api/create-guided-project', { template_id: selectedTemplate, answers })
    setResult(res.data)
    setStep(3)
    setLoading(false)
    if (onProjectCreated) onProjectCreated(res.data.project_id)
  }

  if (step === 0) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 w-full max-w-3xl max-h-[85vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">✨ Proyecto Guiado</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">✕</button>
          </div>
          <p className="text-gray-400 mb-6">Elegí el tipo de proyecto. Te mostraremos exactamente qué archivos se generarán.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.map(t => (
              <button key={t.id} onClick={() => handleSelectTemplate(t.id)}
                className="bg-gray-700/50 border border-gray-600 rounded-xl p-4 text-left hover:border-blue-500 transition group">
                <h3 className="font-bold text-gray-200 group-hover:text-blue-400">{t.name}</h3>
                <p className="text-sm text-gray-400 mt-1">{t.description}</p>
                <div className="mt-3 flex flex-wrap gap-1">
                  {t.files_generated?.slice(0, 5).map(f => (
                    <span key={f} className="text-xs bg-gray-600 text-gray-300 px-2 py-0.5 rounded">{f}</span>
                  ))}
                  {(t.files_generated?.length || 0) > 5 && (
                    <span className="text-xs text-gray-500">+{t.files_generated.length - 5} más</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (step === 1 && questions.length > 0) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 w-full max-w-2xl max-h-[85vh] overflow-y-auto">
          <h2 className="text-2xl font-bold text-white mb-6">Configurá tu proyecto</h2>
          <div className="space-y-4">
            {questions.map(q => (
              <div key={q.id}>
                <label className="block text-sm font-medium text-gray-300 mb-2">{q.question}</label>
                {q.type === 'text' && (
                  <input type="text" defaultValue={q.default || ''} onChange={e => setAnswers(prev => ({ ...prev, [q.id]: e.target.value }))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-200" />
                )}
                {q.type === 'boolean' && (
                  <select defaultValue={q.default ? 'true' : 'false'} onChange={e => setAnswers(prev => ({ ...prev, [q.id]: e.target.value === 'true' }))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-200">
                    <option value="true">Sí</option>
                    <option value="false">No</option>
                  </select>
                )}
                {q.type === 'choice' && (
                  <select defaultValue={q.default || q.options[0]} onChange={e => setAnswers(prev => ({ ...prev, [q.id]: e.target.value }))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-200">
                    {q.options.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                )}
              </div>
            ))}
          </div>
          <div className="flex gap-4 mt-6">
            <button onClick={() => setStep(0)} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg">Volver</button>
            <button onClick={handlePreview} disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50">
              {loading ? 'Generando vista previa...' : 'Vista previa del prompt'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (step === 2 && previewPrompt) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 w-full max-w-2xl max-h-[85vh] overflow-y-auto">
          <h2 className="text-2xl font-bold text-white mb-4">Vista previa del prompt</h2>
          <p className="text-sm text-gray-400 mb-4">Este es el prompt que se enviará a los agentes. Podés editarlo antes de confirmar.</p>
          <textarea value={previewPrompt} onChange={e => setPreviewPrompt(e.target.value)}
            className="w-full h-48 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-gray-200 font-mono text-sm resize-none" />
          <div className="flex gap-4 mt-6">
            <button onClick={() => setStep(1)} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg">Volver</button>
            <button onClick={handleCreate} disabled={loading}
              className="bg-gradient-to-r from-green-600 to-emerald-500 text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50">
              {loading ? 'Creando...' : 'Confirmar y crear proyecto'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (step === 3 && result) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 w-full max-w-md text-center">
          {result.error ? (
            <div>
              <p className="text-red-400 text-lg">{result.error}</p>
              <button onClick={onClose} className="mt-4 bg-gray-700 text-white px-4 py-2 rounded-lg">Cerrar</button>
            </div>
          ) : (
            <div>
              <p className="text-green-400 text-lg font-bold">✅ ¡Proyecto creado!</p>
              <p className="text-gray-400 mt-2">ID: {result.project_id}</p>
              <div className="flex gap-4 justify-center mt-6">
                <button onClick={onClose} className="bg-gray-700 text-white px-4 py-2 rounded-lg">Cerrar</button>
                <button onClick={() => { if (onProjectCreated) onProjectCreated(result.project_id); onClose(); }}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">Abrir proyecto</button>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  return null
}