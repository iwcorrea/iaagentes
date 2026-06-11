import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import api from '../api/axios';
export default function ChatPanel({ project }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const scrollRef = useRef();
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    try {
      const { data } = await api.post('/v1/chat/completions', {
        project_id: project.id,
        message: input
      });
      setMessages(prev => [...prev, { role: 'assistant', content: data.choices[0].message.content }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Could not connect to AI service.' }]);
    }
  };
  return (
    <div className="h-1/2 flex flex-col border-t border-brand-border bg-brand-surface">
      <div className="p-3 border-b border-brand-border font-semibold text-sm">AI Assistant</div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-2 rounded-lg text-sm ${msg.role === 'user' ? 'bg-brand-accent text-white' : 'bg-brand-dark border border-brand-border'}`}>
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={scrollRef} />
      </div>
      <form onSubmit={sendMessage} className="p-3 flex gap-2">
        <input 
          value={input}
          onChange={e => setInput(e.target.value)}
          className="flex-1 bg-brand-dark border border-brand-border p-2 rounded text-sm outline-none focus:border-brand-accent"
          placeholder="Ask about your code..."
        />
        <button className="p-2 bg-brand-accent rounded hover:bg-blue-600 transition"><Send size={16} /></button>
      </form>
    </div>
  );
}