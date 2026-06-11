import { useState } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import ProjectList from './components/ProjectList'
import PreviewPanel from './components/PreviewPanel'
import ConsolePanel from './components/ConsolePanel'
import { ProjectProvider, useProject } from './context/ProjectContext'

function MainContent() {
  const [activeTab, setActiveTab] = useState('chat')
  const { activeProjectId } = useProject()

  const tabs = [
    { id: 'chat', label: 'Chat', icon: '💬' },
    { id: 'projects', label: 'Proyectos', icon: '📁' },
    { id: 'preview', label: 'Vista previa', icon: '👁️' },
    { id: 'console', label: 'Consola', icon: '🖥️' }
  ]

  return (
    <div className="flex flex-1 overflow-hidden">
      {activeProjectId && <Sidebar />}
      <main className="flex-1 flex flex-col overflow-hidden bg-gray-50 dark:bg-gray-900">
        <nav className="flex gap-1 px-4 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition ${
                activeTab === tab.id
                  ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </nav>
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'chat' && <ChatPanel />}
          {activeTab === 'projects' && <ProjectList />}
          {activeTab === 'preview' && <PreviewPanel />}
          {activeTab === 'console' && <ConsolePanel />}
        </div>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <ProjectProvider>
      <div className="h-screen flex flex-col bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors">
        <Header />
        <MainContent />
      </div>
    </ProjectProvider>
  )
}