"""
Gestor de proyectos del ecosistema.
Crea y lista proyectos en la carpeta projects/.
"""

import uuid
from pathlib import Path
from typing import Optional, List


class ProjectManager:
    def __init__(self, base_path: str = "projects"):
        self.base = Path(base_path).resolve()
        self.base.mkdir(parents=True, exist_ok=True)

    def create_project(self, project_id: Optional[str] = None) -> Path:
        """Crea un nuevo proyecto y retorna su ruta."""
        if project_id is None:
            project_id = uuid.uuid4().hex[:8]
        project_path = self.base / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path

    def list_projects(self) -> List[str]:
        """Lista todos los proyectos existentes."""
        return [p.name for p in self.base.iterdir() if p.is_dir()]

    def get_project_path(self, project_id: str) -> Optional[Path]:
        """Obtiene la ruta de un proyecto por su ID."""
        project_path = self.base / project_id
        if project_path.exists():
            return project_path
        return None