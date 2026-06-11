import { createContext, useContext, useState, useEffect } from 'react'
import api from '../api/axios'

const ProjectContext = createContext()

export function ProjectProvider({ children }) {
  const [activeProjectId, setActiveProjectId] = useState(null)
  const [projectName, setProjectName] = useState('')

  useEffect(() => {
    if (activeProjectId) {
      api.get(`/projects/${activeProjectId}/name`)
        .then(res => setProjectName(res.data.name || activeProjectId))
        .catch(() => setProjectName(activeProjectId))
    } else {
      setProjectName('')
    }
  }, [activeProjectId])

  const updateProjectName = async (name) => {
    if (!activeProjectId) return
    await api.put(`/projects/${activeProjectId}/name`, { name })
    setProjectName(name)
  }

  return (
    <ProjectContext.Provider value={{ activeProjectId, setActiveProjectId, projectName, updateProjectName }}>
      {children}
    </ProjectContext.Provider>
  )
}

export function useProject() {
  return useContext(ProjectContext)
}