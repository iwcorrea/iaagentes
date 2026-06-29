"""
Gestor de proyectos. Permite crear carpetas con nombre personalizado
y recuperar rutas por nombre o ID.
"""
from pathlib import Path
from typing import Optional

class ProjectManager:
    def __init__(self, base_dir: str = "projects"):
        self.base = Path(base_dir)
        self.base.mkdir(exist_ok=True)

    def create_project(self, name: Optional[str] = None) -> Path:
        """Crea una carpeta de proyecto. Si se da un nombre, lo usa; si no, genera un ID."""
        if name:
            project_path = self.base / name
        else:
            import uuid
            project_path = self.base / uuid.uuid4().hex[:8]

        project_path.mkdir(parents=True, exist_ok=True)
        return project_path

    def get_project_path(self, project_id: str) -> Optional[Path]:
        """Busca la carpeta del proyecto por nombre o ID (cualquier carpeta que contenga el texto)."""
        for d in self.base.iterdir():
            if d.is_dir() and (d.name == project_id or project_id in d.name):
                return d
        return None

    def list_projects(self) -> list:
        """Devuelve nombres de las carpetas de proyectos existentes."""
        return [d.name for d in self.base.iterdir() if d.is_dir()]