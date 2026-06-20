import React from 'react';
import { useProject } from '../context/ProjectContext';
import ProjectList from '../components/ProjectList';
import ChatPanel from '../components/ChatPanel';

const Dashboard = () => {
  const { selectedProject } = useProject();

  return (
    <div className="flex h-full gap-4">
      <div className="w-80 flex-shrink-0">
        <ProjectList />
      </div>
      <div className="flex-1 flex flex-col">
        <ChatPanel />
      </div>
    </div>
  );
};

export default Dashboard;