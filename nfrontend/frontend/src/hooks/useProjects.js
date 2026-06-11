import { useState } from 'react';
import api from '../api/axios';
export function useProjects() {
  const [loading, setLoading] = useState(false);
  const createProject = async (name) => {
    setLoading(true);
    try {
      const res = await api.post('/projects', { name });
      return res.data;
    } finally {
      setLoading(false);
    }
  };
  return { createProject, loading };
}