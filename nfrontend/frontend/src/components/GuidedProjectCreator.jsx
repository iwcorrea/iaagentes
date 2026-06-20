import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { Rocket, Loader2 } from 'lucide-react';
import api from '../api/axios';

const GuidedProjectCreator = () => {
  const { createProject } = useProject();
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await api.get('/api/guided-templates');
        setTemplates(response.data?.templates || []);
      } catch (error) {
        console.error('Error fetching templates:', error);
      }
    };
    fetchTemplates();
  }, []);

  useEffect(() => {
    if (!selectedTemplate) {
      setQuestions([]);
      setAnswers({});
      return;
    }
    const fetchQuestions = async () => {
      try {
        const response = await api.get(`/api/guided-questions/${selectedTemplate}`);
        setQuestions(response.data?.questions || []);
        setAnswers({});
      } catch (error) {
        console.error('Error fetching questions:', error);
      }
    };
    fetchQuestions();
  }, [selectedTemplate]);

  const handleAnswerChange = (questionId, value) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleCreate = async () => {
    setCreating(true);
    try {
      const response = await api.post('/api/create-guided-project', {
        template_id: selectedTemplate,
        answers,
      });
      await createProject(response.data.prompt);
    } catch (error) {
      console.error('Error creating guided project:', error);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-4">
      <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
        <Rocket className="w-5 h-5" />
        Asistente de Creación Guiada
      </h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tipo de Proyecto
          </label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Selecciona un tipo...</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        {questions.length > 0 && (
          <div className="space-y-3">
            <h3 className="font-medium text-gray-700">Responde las preguntas:</h3>
            {questions.map((q) => (
              <div key={q.id}>
                <label className="block text-sm text-gray-600 mb-1">{q.question}</label>
                <input
                  type="text"
                  value={answers[q.id] || ''}
                  onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={q.placeholder || 'Escribe tu respuesta...'}
                />
              </div>
            ))}
            <button
              onClick={handleCreate}
              disabled={creating || Object.keys(answers).length !== questions.length}
              className="w-full px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:bg-gray-400 transition-colors flex items-center justify-center gap-2"
            >
              {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Rocket className="w-4 h-4" />}
              {creating ? 'Creando...' : 'Crear Proyecto'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default GuidedProjectCreator;