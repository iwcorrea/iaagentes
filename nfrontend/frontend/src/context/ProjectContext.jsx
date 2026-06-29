import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import api from '../api/axios'

const ProjectContext = createContext()

export function ProjectProvider({ children }) {
  const [activeProjectId, setActiveProjectId] = useState(() => localStorage.getItem('activeProjectId') || null)
  const [projectName, setProjectName] = useState('')
  const [chatMessages, setChatMessages] = useState([])
  const [executionUrl, setExecutionUrl] = useState(null)
  const [projectFiles, setProjectFiles] = useState([])
  const [projectStats, setProjectStats] = useState({ files: 0, lastGeneration: null })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (activeProjectId) localStorage.setItem('activeProjectId', activeProjectId)
    else localStorage.removeItem('activeProjectId')
  }, [activeProjectId])

  useEffect(() => {
    if (!activeProjectId) {
      setProjectName(''); setChatMessages([]); setExecutionUrl(null)
      setProjectFiles([]); setProjectStats({ files: 0, lastGeneration: null }); setError(null)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)

    const load = async () => {
      try {
        const [nameRes, chatRes, filesRes] = await Promise.all([
          api.get(`/api/projects/${activeProjectId}/name`),
          api.get(`/api/projects/${activeProjectId}/chat`),
          api.get(`/api/projects/${activeProjectId}/files`)
        ])
        if (cancelled) return
        setProjectName(nameRes.data.name || activeProjectId)
        setChatMessages(chatRes.data.messages || [])
        const files = filesRes.data.files || []
        setProjectFiles(files)
        setProjectStats({ files: files.length, lastGeneration: files.length > 0 ? new Date().toISOString() : null })
      } catch (err) {
        if (!cancelled) {
          setError('Error al cargar datos del proyecto')
          console.error('ProjectContext load error:', err)
          // No vaciar archivos previos
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [activeProjectId])

  const updateProjectName = useCallback(async (name) => {
    if (!activeProjectId) return
    try {
      await api.put(`/api/projects/${activeProjectId}/name`, { name })
      setProjectName(name)
    } catch (err) { setError('Error al actualizar el nombre') }
  }, [activeProjectId])

  return (
    <ProjectContext.Provider value={{
      activeProjectId, setActiveProjectId, projectName, updateProjectName,
      chatMessages, setChatMessages, executionUrl, setExecutionUrl,
      projectFiles, projectStats, loading, error, setError
    }}>
      {children}
    </ProjectContext.Provider>
  )
}

export function useProject() {
  const ctx = useContext(ProjectContext)
  if (!ctx) throw new Error('useProject debe usarse dentro de un ProjectProvider')
  return ctx
}