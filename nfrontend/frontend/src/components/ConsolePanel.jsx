import React, { useRef, useEffect } from 'react';
import { Terminal } from 'lucide-react';

const ConsolePanel = ({ logs = [] }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  if (!logs || logs.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <Terminal className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>No hay logs disponibles</p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="h-full overflow-y-auto p-4 bg-gray-900 text-green-400 font-mono text-sm"
    >
      {logs.map((log, index) => (
        <div key={index} className="py-0.5">
          <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>
          <span className="ml-2">{log}</span>
        </div>
      ))}
    </div>
  );
};

export default ConsolePanel;