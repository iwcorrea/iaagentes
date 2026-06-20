import React from 'react';
import { useProject } from '../context/ProjectContext';
import { Users, Cpu, CheckCircle, Clock, AlertCircle } from 'lucide-react';

const TeamPanel = () => {
  const { agentStatus } = useProject();

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'pending': return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <Cpu className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="h-full overflow-y-auto p-4">
      <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
        <Users className="w-5 h-5" />
        Estado de los Agentes
      </h2>

      {!agentStatus || Object.keys(agentStatus).length === 0 ? (
        <p className="text-gray-500">No hay agentes activos</p>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(agentStatus).map(([name, info]) => (
            <div
              key={name}
              className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-800">{name}</span>
                {getStatusIcon(info?.status)}
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {info?.current_task || 'Esperando tarea...'}
              </p>
              {info?.emoji && (
                <span className="text-2xl mt-2 block">{info.emoji}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TeamPanel;