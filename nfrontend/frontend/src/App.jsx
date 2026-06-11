import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatPanel from './components/ChatPanel';
import ProjectList from './components/ProjectList';
import ImprovementsPanel from './components/ImprovementsPanel';
import PreviewPanel from './components/PreviewPanel';
import ConsolePanel from './components/ConsolePanel';
import CodeViewer from './components/CodeViewer';
import Toast from './components/Toast';
import api from './api/axios';
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
};
function App() {
  const [activeProject, setActiveProject] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [notification, setNotification] = useState(null);
  const notify = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };
  return (
    <div className="h-screen flex flex-col">
      <Header onLogout={() => { localStorage.clear(); window.location.href = '/login'; }} />
      <div className="flex-1 flex overflow-hidden">
        <Routes>
          <Route path="/login" element={<Login notify={notify} />} />
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <div className="flex w-full h-full">
                  <Sidebar 
                    onSelectProject={setActiveProject} 
                    activeProject={activeProject} 
                    onSelectFile={setSelectedFile}
                    selectedFile={selectedFile}
                  />
                  <main className="flex-1 flex flex-col overflow-hidden">
                    {!activeProject ? (
                      <ProjectList onOpenProject={setActiveProject} notify={notify} />
                    ) : (
                      <div className="flex h-full">
                        <div className="flex-1 flex flex-col border-r border-brand-border">
                          <CodeViewer file={selectedFile} project={activeProject} />
                          <ConsolePanel project={activeProject} />
                        </div>
                        <div className="w-1/3 flex flex-col">
                          <ChatPanel project={activeProject} />
                          <ImprovementsPanel project={activeProject} />
                        </div>
                        <PreviewPanel project={activeProject} />
                      </div>
                    )}
                  </main>
                </div>
              </ProtectedRoute>
            } 
          />
        </Routes>
      </div>
      <Toast notification={notification} />
    </div>
  );
}
function Login({ notify }) {
  const [form, setForm] = useState({ email: '', password: '' });
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const { data } = await api.post('/auth/token', {
        username: form.email,
        password: form.password
      });
      localStorage.setItem('token', data.access_token);
      window.location.href = '/';
    } catch (err) {
      notify(err.response?.data?.detail || 'Login failed', 'error');
    }
  };
  return (
    <div className="h-full flex items-center justify-center bg-brand-dark">
      <form onSubmit={handleLogin} className="bg-brand-surface p-8 rounded-xl border border-brand-border w-96 space-y-4">
        <h2 className="text-2xl font-bold mb-6 text-center">Welcome Back</h2>
        <input 
          className="w-full p-2 rounded bg-brand-dark border border-brand-border text-white" 
          placeholder="Email" 
          onChange={e => setForm({...form, email: e.target.value})}
        />
        <input 
          type="password" 
          className="w-full p-2 rounded bg-brand-dark border border-brand-border text-white" 
          placeholder="Password" 
          onChange={e => setForm({...form, password: e.target.value})}
        />
        <button type="submit" className="w-full bg-brand-accent p-2 rounded font-bold hover:bg-blue-600 transition">Login</button>
      </form>
    </div>
  );
}
export default App;