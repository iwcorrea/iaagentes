import React, { useEffect, useState } from 'react';
import { useProject } from '../context/ProjectContext';
import ProjectList from './ProjectList';
import ChatPanel from './ChatPanel';
import ConsolePanel from './ConsolePanel';
import PreviewPanel from './PreviewPanel';
import SettingsPanel from './SettingsPanel';
import TeamPanel from './TeamPanel';
import GuidedProjectCreator from './GuidedProjectCreator';

const ProjectDashboard = () => {
  const { selectedProject, consoleOutput } = useProject();
  const [activeTab, setActiveTab] = useState('chat');

  const tabs = [
    { id: 'chat', label: '💬 Chat' },
    { id: 'preview', label: '👁️ Vista Previa' },
    { id: 'console', label: '📟 Consola' },
    { id: 'team', label: '🤖 Agentes' },
    { id: 'settings', label: '⚙️ Configuración' },
    { id: 'guided', label: '🚀 Asistente' },
  ];

  return (
    <div className="flex h-full gap-4">
      {/* Barra lateral izquierda - lista de proyectos */}
      <div className="w-72 flex-shrink-0">
        <ProjectList />
      </div>

      {/* Contenido principal */}
      <div className="flex-1 flex flex-col bg-white rounded-lg shadow-sm overflow-hidden">
        {/* Tabs de navegación */}
        <div className="flex border-b bg-gray-50 px-2 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Contenido del tab activo */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'chat' && <ChatPanel />}
          {activeTab === 'preview' && <PreviewPanel project={selectedProject} />}
          {activeTab === 'console' && <ConsolePanel logs={consoleOutput} />}
          {activeTab === 'team' && <TeamPanel />}
          {activeTab === 'settings' && <SettingsPanel />}
          {activeTab === 'guided' && <GuidedProjectCreator />}
        </div>
      </div>
    </div>
  );
};

export default ProjectDashboard;