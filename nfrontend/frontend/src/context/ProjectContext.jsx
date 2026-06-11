import { createContext, useContext, useState } from 'react'

const ProjectContext = createContext()

export function ProjectProvider({ children }) {
  const [activeProjectId, setActiveProjectId] = useState(null)

  return (
    <ProjectContext.Provider value={{ activeProjectId, setActiveProjectId }}>
      {children}
    </ProjectContext.Provider>
  )
}

export function useProject() {
  return useContext(ProjectContext)
}