import { useState } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import ProjectList from './components/ProjectList'
import ImprovementsPanel from './components/ImprovementsPanel'
import PreviewPanel from './components/PreviewPanel'
import ConsolePanel from './components/ConsolePanel'

export default function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [activeProjectId, setActiveProjectId] = useState(null)

  const handleOpenProject = (id) => {
    setActiveProjectId(id)
    setActiveTab('chat')
  }

  const handleCloseProject = () => {
    setActiveProjectId(null)
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors">
      <Header activeProjectId={activeProjectId} onCloseProject={handleCloseProject} />
      <div className="flex flex-1 overflow-hidden">
        {activeProjectId && (
          <Sidebar projectId={activeProjectId} onClose={handleCloseProject} />
        )}
        <main className="flex-1 flex flex-col overflow-hidden">
          <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 flex gap-1 overflow-x-auto">
            {[
              { id: 'chat', label: '💬 Chat' },
              { id: 'projects', label: '📁 Proyectos' },
              { id: 'improvements', label: '💡 Mejoras' },
              { id: 'preview', label: '👁️ Vista previa' },
              { id: 'console', label: '🖥️ Consola' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-4 text-sm font-medium whitespace-nowrap border-b-2 transition ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'chat' && <ChatPanel projectId={activeProjectId} />}
            {activeTab === 'projects' && <ProjectList onOpen={handleOpenProject} />}
            {activeTab === 'improvements' && <ImprovementsPanel projectId={activeProjectId} />}
            {activeTab === 'preview' && <PreviewPanel projectId={activeProjectId} />}
            {activeTab === 'console' && <ConsolePanel projectId={activeProjectId} />}
          </div>
        </main>
      </div>
    </div>
  )
}