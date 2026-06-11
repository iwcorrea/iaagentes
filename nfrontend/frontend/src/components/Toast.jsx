import React from 'react';
export default function Toast({ notification }) {
  if (!notification) return null;
  const colors = {
    info: 'bg-blue-600',
    error: 'bg-red-600',
    success: 'bg-green-600'
  };
  return (
    <div className={`fixed bottom-4 right-4 ${colors[notification.type]} text-white px-4 py-2 rounded-lg shadow-lg transition-all animate-bounce text-sm`}>
      {notification.message}
    </div>
  );
}