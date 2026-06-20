import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../api/axios';

const ProjectContext = createContext();

export const ProjectProvider = ({ children }) => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [consoleOutput, setConsoleOutput] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [agentStatus, setAgentStatus] = useState({});
  const [progress, setProgress] = useState(0);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/api/projects');
      const data = Array.isArray(response.data) ? response.data : [];
      setProjects(data);
      if (data.length > 0 && !selectedProject) {
        setSelectedProject(data[0]);
      }
      return data;
    } catch (err) {
      console.error('Error fetching projects:', err);
      setError('No se pudieron cargar los proyectos');
      setProjects([]);
      return [];
    } finally {
      setLoading(false);
    }
  };

  const createProject = async (prompt) => {
    try {
      const response = await api.post('/api/projects', { prompt });
      const newProject = response.data;
      setProjects((prev) => [...prev, newProject]);
      setSelectedProject(newProject);
      return newProject;
    } catch (err) {
      console.error('Error creating project:', err);
      throw err;
    }
  };

  const selectProject = (project) => {
    setSelectedProject(project);
  };

  const fetchAgentStatus = async () => {
    try {
      const response = await api.get('/api/agents');
      setAgentStatus(response.data || {});
      if (response.data?.progress !== undefined) {
        setProgress(response.data.progress);
      }
    } catch (err) {
      console.error('Error fetching agent status:', err);
      // No mostrar error al usuario, solo log
    }
  };

  const fetchProgress = async () => {
    try {
      const response = await api.get('/api/progress');
      if (response.data?.progress !== undefined) {
        setProgress(response.data.progress);
      }
    } catch (err) {
      console.error('Error fetching progress:', err);
    }
  };

  useEffect(() => {
    fetchProjects();
    const interval = setInterval(() => {
      fetchAgentStatus();
      fetchProgress();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <ProjectContext.Provider
      value={{
        projects,
        selectedProject,
        consoleOutput,
        loading,
        error,
        agentStatus,
        progress,
        fetchProjects,
        createProject,
        selectProject,
        setConsoleOutput,
        fetchAgentStatus,
        fetchProgress,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};