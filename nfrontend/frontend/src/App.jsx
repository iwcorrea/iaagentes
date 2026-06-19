import { useState } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import ProjectList from './components/ProjectList'
import PreviewPanel from './components/PreviewPanel'
import ConsolePanel from './components/ConsolePanel'
import TeamPanel from './components/TeamPanel'
import SettingsPanel from './components/SettingsPanel'
import ProjectDashboard from './components/ProjectDashboard'
import { ProjectProvider, useProject } from './context/ProjectContext'

function MainContent() {
  const [activeTab, setActiveTab] = useState('chat')
  const { activeProjectId } = useProject()

  const tabs = [
    { id: 'chat', label: 'Chat', icon: '💬' },
    { id: 'projects', label: 'Proyectos', icon: '📁' },
    { id: 'team', label: 'Equipo', icon: '👥' },
    { id: 'dashboard', label: 'Dashboard', icon: '📊', requiresProject: true },
    { id: 'preview', label: 'Vista previa', icon: '👁️', requiresProject: true },
    { id: 'console', label: 'Consola', icon: '🖥️', requiresProject: true },
    { id: 'settings', label: 'Configuración', icon: '⚙️' }
  ]

  return (
    <div className="flex flex-1 overflow-hidden">
      {activeProjectId && <Sidebar />}
      <main className="flex-1 flex flex-col overflow-hidden bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
        <nav className="flex gap-1 px-6 py-3 bg-gray-800/50 backdrop-blur-sm border-b border-gray-700/50">
          {tabs.filter(tab => !tab.requiresProject || activeProjectId).map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-5 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-cyan-600/20 text-cyan-400 shadow-lg shadow-cyan-500/10 border border-cyan-500/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/30'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'chat' && <ChatPanel />}
          {activeTab === 'projects' && <ProjectList />}
          {activeTab === 'team' && <TeamPanel />}
          {activeTab === 'dashboard' && <ProjectDashboard />}
          {activeTab === 'preview' && <PreviewPanel />}
          {activeTab === 'console' && <ConsolePanel />}
          {activeTab === 'settings' && <SettingsPanel />}
        </div>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <ProjectProvider>
      <div className="h-screen flex flex-col bg-gradient-to-br from-slate-900 to-gray-900 text-gray-100">
        <Header />
        <MainContent />
      </div>
    </ProjectProvider>
  )
}