import { useState, useEffect } from 'react'
import api from '../api/axios'

export default function GuidedProjectCreator({ onClose, onProjectCreated }) {
  const [step, setStep] = useState(0)
  const [projectTypes, setProjectTypes] = useState([])
  const [selectedType, setSelectedType] = useState('')
  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    api.get('/api/project-types')
      .then(res => setProjectTypes(res.data.types || []))
      .catch(() => {
        // Fallback offline
        setProjectTypes([
          { id: 'web_app', name: 'App Web Full-Stack', description: 'Backend + Frontend' },
          { id: 'api_rest', name: 'API REST', description: 'Solo backend' },
          { id: 'mobile_app', name: 'App Móvil', description: 'PWA o React Native' },
          { id: 'landing_page', name: 'Landing Page', description: 'Sitio web estático' }
        ])
      })
  }, [])

  const handleSelectType = async (typeId) => {
    setSelectedType(typeId)
    setAnswers({})
    try {
      const res = await api.get(`/api/project-questions/${typeId}`)
      setQuestions(res.data.questions || [])
    } catch {
      // Preguntas por defecto si el backend no responde
      const predefined = {
        web_app: [
          { id: 'project_name', question: '¿Nombre del proyecto?', type: 'text', default: 'MiApp' },
          { id: 'auth_required', question: '¿Autenticación de usuarios?', type: 'boolean', default: true },
          { id: 'database', question: '¿Base de datos?', type: 'choice', options: ['sqlite', 'postgresql'], default: 'sqlite' },
          { id: 'frontend', question: '¿Framework Frontend?', type: 'choice', options: ['react', 'vue'], default: 'react' },
        ],
        api_rest: [
          { id: 'project_name', question: '¿Nombre de la API?', type: 'text', default: 'MiAPI' },
          { id: 'auth_required', question: '¿Autenticación JWT?', type: 'boolean', default: true },
          { id: 'database', question: '¿Base de datos?', type: 'choice', options: ['sqlite', 'postgresql'], default: 'sqlite' },
        ],
        mobile_app: [
          { id: 'project_name', question: '¿Nombre de la app?', type: 'text', default: 'MiApp' },
          { id: 'offline_mode', question: '¿Soporte offline?', type: 'boolean', default: false },
        ],
        landing_page: [
          { id: 'project_name', question: '¿Nombre del sitio?', type: 'text', default: 'MiLanding' },
          { id: 'animations', question: '¿Animaciones?', type: 'boolean', default: true },
        ]
      }
      setQuestions(predefined[typeId] || [])
    }
    setStep(2)
  }

  const handleAnswer = (questionId, value) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }))
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const res = await api.post('/api/create-guided-project', {
        project_type: selectedType,
        answers: answers
      })
      setResult(res.data)
      if (onProjectCreated) onProjectCreated(res.data.project_id)
    } catch (err) {
      setResult({ error: 'Error al crear el proyecto' })
    } finally {
      setLoading(false)
    }
  }

  if (step === 0) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto shadow-2xl">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">✨ Nuevo Proyecto Guiado</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-white transition text-xl">✕</button>
          </div>
          <p className="text-gray-400 mb-6">Seleccioná el tipo de proyecto que querés crear:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projectTypes.map(type => (
              <button
                key={type.id}
                onClick={() => handleSelectType(type.id)}
                className="bg-gray-700/50 border border-gray-600 rounded-xl p-4 text-left hover:border-blue-500 transition group"
              >
                <h3 className="font-bold text-gray-200 group-hover:text-blue-400">{type.name}</h3>
                <p className="text-sm text-gray-400 mt-1">{type.description}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (step === 2 && questions.length > 0) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto shadow-2xl">
          <h2 className="text-2xl font-bold text-white mb-6">Configurá tu proyecto</h2>
          <div className="space-y-4">
            {questions.map(q => (
              <div key={q.id}>
                <label className="block text-sm font-medium text-gray-300 mb-2">{q.question}</label>
                {q.type === 'text' && (
                  <input
                    type="text"
                    defaultValue={q.default || ''}
                    onChange={e => handleAnswer(q.id, e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-200"
                  />
                )}
                {q.type === 'boolean' && (
                  <select
                    defaultValue={q.default ? 'true' : 'false'}
                    onChange={e => handleAnswer(q.id, e.target.value === 'true')}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-200"
                  >
                    <option value="true">Sí</option>
                    <option value="false">No</option>
                  </select>
                )}
                {q.type === 'choice' && (
                  <select
                    defaultValue={q.default || (q.options ? q.options[0] : '')}
                    onChange={e => handleAnswer(q.id, e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-gray-200"
                  >
                    {(q.options || []).map(opt => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                )}
              </div>
            ))}
          </div>
          <div className="flex gap-4 mt-6">
            <button onClick={() => setStep(0)} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition">Volver</button>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50 transition"
            >
              {loading ? 'Creando...' : 'Crear Proyecto'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (result) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 w-full max-w-md text-center shadow-2xl">
          {result.error ? (
            <div>
              <p className="text-red-400 text-lg">{result.error}</p>
              <button onClick={onClose} className="mt-4 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition">Cerrar</button>
            </div>
          ) : (
            <div>
              <p className="text-green-400 text-lg font-bold">✅ ¡Proyecto creado!</p>
              <p className="text-gray-400 mt-2">ID: {result.project_id}</p>
              <div className="flex gap-4 justify-center mt-6">
                <button onClick={onClose} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition">Cerrar</button>
                <button
                  onClick={() => {
                    if (onProjectCreated) onProjectCreated(result.project_id)
                    onClose()
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
                >
                  Abrir Proyecto
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  return null
}