import React, { useState, useEffect, useRef } from 'react';
import { useProject } from '../context/ProjectContext';
import api from '../api/axios';
import { Send, Loader2 } from 'lucide-react';

const ChatPanel = () => {
  const { selectedProject } = useProject();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Cargar historial cuando se selecciona un proyecto
  useEffect(() => {
    if (!selectedProject) {
      setMessages([]);
      return;
    }

    const fetchChatHistory = async () => {
      setLoading(true);
      try {
        const response = await api.get(`/api/projects/${selectedProject.id}/chat`);
        // Asegurar que siempre sea un array
        const history = Array.isArray(response.data) ? response.data : [];
        setMessages(history);
      } catch (error) {
        console.error('Error al cargar historial del chat:', error);
        setMessages([]);
      } finally {
        setLoading(false);
      }
    };

    fetchChatHistory();
  }, [selectedProject]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading || !selectedProject) return;

    const userMessage = { role: 'user', content: input.trim() };
    // Optimistic update
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.post(`/api/projects/${selectedProject.id}/chat`, {
        message: userMessage.content,
      });
      const assistantMessage = response.data?.message || { 
        role: 'assistant', 
        content: 'No se recibió respuesta del servidor.' 
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error al enviar mensaje:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '❌ Error al comunicarse con el servidor.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!selectedProject) {
    return (
      <div className="flex items-center justify-center h-full bg-white rounded-lg shadow-sm">
        <p className="text-gray-500">Selecciona un proyecto para comenzar a chatear</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm">
      <div className="border-b px-4 py-3 bg-gray-50 rounded-t-lg">
        <h3 className="font-semibold text-gray-700">
          Chat con Agentes - {selectedProject.name}
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>No hay mensajes aún. Comienza una conversación.</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} mb-3`}
            >
              <div
                className={`max-w-[70%] rounded-lg px-4 py-2 ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-800'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t p-3 bg-gray-50 rounded-b-lg">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Escribe tu mensaje..."
            disabled={loading}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Enviar
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatPanel;