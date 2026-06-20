import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { Settings, Save } from 'lucide-react';
import api from '../api/axios';

const SettingsPanel = () => {
  const [settings, setSettings] = useState({
    models: { primary: 'local-coder', temperature: 0.0, max_tokens: 4096 },
    agents: {},
    teams: []
  });
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const { fetchAgentStatus } = useProject();

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await api.get('/api/settings');
        setSettings(response.data);
      } catch (error) {
        console.error('Error fetching settings:', error);
      }
    };
    fetchSettings();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      await api.put('/api/settings', settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      await fetchAgentStatus();
    } catch (error) {
      console.error('Error saving settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (section, key, value) => {
    setSettings((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
  };

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-700 flex items-center gap-2">
          <Settings className="w-5 h-5" />
          Configuración del Sistema
        </h2>
        <button
          onClick={handleSave}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-400 transition-colors flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {loading ? 'Guardando...' : 'Guardar'}
        </button>
      </div>

      {saved && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-md">
          Configuración guardada correctamente
        </div>
      )}

      <div className="space-y-6">
        {/* Modelos */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-700 mb-3">Modelos de IA</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Modelo Principal</label>
              <select
                value={settings.models?.primary || 'local-coder'}
                onChange={(e) => handleChange('models', 'primary', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="local-coder">Local Coder (Ollama)</option>
                <option value="cloud-coder">Cloud Coder (OpenRouter)</option>
                <option value="hibrido-coder">Híbrido</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Temperatura</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={settings.models?.temperature || 0}
                onChange={(e) => handleChange('models', 'temperature', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;