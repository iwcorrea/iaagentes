import { useState, useEffect, useCallback } from 'react'
import api from '../api/axios'
import { useProject } from '../context/ProjectContext'

export default function ProjectExplorer({ onSelectFile }) {
  const { activeProjectId, projectFiles } = useProject()
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedDirs, setExpandedDirs] = useState(new Set())

  useEffect(() => {
    if (!activeProjectId) {
      setFiles([])
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    api.get(`/api/projects/${activeProjectId}/files`)
      .then(res => { if (!cancelled) setFiles(res.data.files || []) })
      .catch(err => {
        console.error('Error cargando archivos:', err)
        if (!cancelled) setFiles([])
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [activeProjectId, projectFiles])

  const toggleDir = useCallback((dir) => {
    setExpandedDirs(prev => {
      const next = new Set(prev)
      next.has(dir) ? next.delete(dir) : next.add(dir)
      return next
    })
  }, [])

  const buildTree = () => {
    const tree = {}
    files.forEach(file => {
      const parts = file.split('/')
      let current = tree
      parts.forEach((part, i) => {
        if (i === parts.length - 1) {
          if (!current._files) current._files = []
          current._files.push(part)
        } else {
          if (!current[part]) current[part] = {}
          current = current[part]
        }
      })
    })
    return tree
  }

  const renderTree = (tree, path = '') => {
    const entries = Object.entries(tree).filter(([key]) => key !== '_files')
    const fileList = tree._files || []
    return (
      <>
        {entries.map(([name, subtree]) => {
          const fullPath = path ? `${path}/${name}` : name
          const isExpanded = expandedDirs.has(fullPath)
          return (
            <div key={fullPath}>
              <div className="flex items-center gap-1 py-1 px-2 hover:bg-gray-700 cursor-pointer rounded text-sm" onClick={() => toggleDir(fullPath)}>
                <span className="text-xs">{isExpanded ? '📂' : '📁'}</span>
                <span className="text-gray-300">{name}</span>
              </div>
              {isExpanded && <div className="ml-4 border-l border-gray-600 pl-2">{renderTree(subtree, fullPath)}</div>}
            </div>
          )
        })}
        {fileList.map(file => {
          const fullPath = path ? `${path}/${file}` : file
          const ext = file.split('.').pop()?.toLowerCase()
          const icon = { py:'🐍', jsx:'⚛️', js:'📜', css:'🎨', html:'🌐', json:'📋', md:'📝', yml:'⚙️', yaml:'⚙️', env:'🔐', txt:'📄', dockerfile:'🐳' }[ext] || '📄'
          return (
            <div key={fullPath} className="flex items-center gap-1 py-1 px-2 hover:bg-gray-700 cursor-pointer rounded text-sm ml-4" onClick={() => onSelectFile && onSelectFile(fullPath)}>
              <span className="text-xs">{icon}</span>
              <span className="text-gray-300 truncate">{file}</span>
            </div>
          )
        })}
      </>
    )
  }

  if (loading) return <div className="p-4 text-gray-400"><div className="animate-spin h-4 w-4 border-b-2 border-cyan-400 rounded-full inline-block mr-2"></div>Cargando archivos...</div>
  if (!activeProjectId) return <p className="p-4 text-gray-500">Seleccioná un proyecto para ver sus archivos.</p>
  if (files.length === 0) return <p className="p-4 text-gray-500">No hay archivos generados aún.</p>

  const tree = buildTree()
  return (
    <div className="p-3 text-gray-300 overflow-y-auto h-full">
      <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">📁 Archivos del proyecto</h3>
      {renderTree(tree)}
    </div>
  )
}