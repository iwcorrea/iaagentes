import React, { useState, useEffect } from 'react';

function App() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const checkHealth = async () => {
    setLoading(true);
    try {
      const response = await fetch('/health');
      const data = await response.json();
      setStatus(data.status);
    } catch (error) {
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">FastAPI Health Check</h1>
      {loading ? (
        <p className="animate-spin rounded-full border-4 border-blue-500 border-t-transparent h-12 w-12"></p>
      ) : (
        <>
          <p className="text-lg text-gray-600">Status: 
            {status === 'ok' ? (
              <span className="text-green-600 font-medium">{status}</span>
            ) : status === 'error' ? (
              <span className="text-red-600 font-medium">{status}</span>
            ) : (
              <span className="text-yellow-600 font-medium">checking...</span>
            )}
          </p>
          {!loading && status !== 'ok' && (
            <button
              onClick={checkHealth}
              className="mt-4 px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition"
            >
              Retry
            </button>
          )}
        </>
      )}
    </div>
  );
}

export default App;