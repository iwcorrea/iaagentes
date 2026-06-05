import uuid
from pathlib import Path
from typing import Optional

class ProjectManager:
    """
    Administra espacios de trabajo aislados para múltiples proyectos.
    """

    def __init__(self, base_path: str = "workspace"):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def create_project(self, project_id: Optional[str] = None) -> Path:
        """Crea (o reutiliza) un directorio de proyecto y devuelve su ruta."""
        if project_id is None:
            project_id = str(uuid.uuid4())[:8]
        project_path = self.base / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path

    def list_projects(self):
        """Lista los IDs de proyectos existentes."""
        if not self.base.exists():
            return []
        return [d.name for d in self.base.iterdir() if d.is_dir()]