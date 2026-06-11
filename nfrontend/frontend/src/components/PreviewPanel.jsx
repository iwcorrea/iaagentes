import { useProject } from '../context/ProjectContext'

export default function PreviewPanel() {
  const { activeProjectId } = useProject()

  if (!activeProjectId) return <div className="p-4 text-gray-500">Abrí un proyecto para ver la vista previa.</div>

  return (
    <div className="h-full p-4">
      <iframe src="http://localhost:8001" className="w-full h-full rounded-xl border border-gray-300 dark:border-gray-600" />
    </div>
  )
}