import { createContext, useContext, useState, useEffect } from 'react'
import api from '../api/axios'

const ProjectContext = createContext()

export function ProjectProvider({ children }) {
  const [activeProjectId, setActiveProjectId] = useState(null)
  const [projectName, setProjectName] = useState('')
  const [chatMessages, setChatMessages] = useState([])
  const [executionUrl, setExecutionUrl] = useState(null)
  const [projectFiles, setProjectFiles] = useState([])
  const [projectStats, setProjectStats] = useState({ files: 0, lastGeneration: null })

  useEffect(() => {
    if (activeProjectId) {
      api.get(`/projects/${activeProjectId}/name`)
        .then(res => setProjectName(res.data.name || activeProjectId))
        .catch(() => setProjectName(activeProjectId))
      api.get(`/projects/${activeProjectId}/chat`)
        .then(res => setChatMessages(res.data.messages || []))
        .catch(() => setChatMessages([]))
      api.get(`/projects/${activeProjectId}/files`)
        .then(res => {
          const files = res.data.files || []
          setProjectFiles(files)
          setProjectStats({ files: files.length, lastGeneration: new Date().toISOString() })
        })
        .catch(() => setProjectFiles([]))
    } else {
      setProjectName('')
      setChatMessages([])
      setExecutionUrl(null)
      setProjectFiles([])
      setProjectStats({ files: 0, lastGeneration: null })
    }
  }, [activeProjectId])

  const updateProjectName = async (name) => {
    if (!activeProjectId) return
    await api.put(`/projects/${activeProjectId}/name`, { name })
    setProjectName(name)
  }

  return (
    <ProjectContext.Provider value={{ 
      activeProjectId, setActiveProjectId, 
      projectName, updateProjectName,
      chatMessages, setChatMessages,
      executionUrl, setExecutionUrl,
      projectFiles, projectStats
    }}>
      {children}
    </ProjectContext.Provider>
  )
}

export function useProject() {
  return useContext(ProjectContext)
}