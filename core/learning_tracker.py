"""
Rastreador de aprendizaje por proyecto.
Guarda un resumen de cada generación para que los agentes aprendan
y no repitan errores en futuros proyectos.
"""
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

TRACKER_FILE = Path("learning_tracker.json")


class LearningTracker:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        if TRACKER_FILE.exists():
            try:
                return json.loads(TRACKER_FILE.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError):
                return {"projects": []}
        return {"projects": []}

    def _save(self):
        TRACKER_FILE.write_text(json.dumps(self._data, indent=2), encoding='utf-8')

    def add_project(self, project_id: str, summary: Dict[str, Any]):
        """Registra un proyecto generado con su resumen."""
        entry = {
            "project_id": project_id,
            "timestamp": datetime.now().isoformat(),
            "summary": summary
        }
        self._data["projects"].append(entry)
        self._save()

    def get_insights(self) -> Dict[str, Any]:
        """Retorna estadísticas útiles para mejorar futuras generaciones."""
        projects = self._data.get("projects", [])
        if not projects:
            return {}

        total = len(projects)
        avg_files = sum(len(p.get("summary", {}).get("files", [])) for p in projects) / total if total > 0 else 0
        common_errors = {}
        for p in projects:
            for error in p.get("summary", {}).get("errors", []):
                common_errors[error] = common_errors.get(error, 0) + 1

        return {
            "total_projects": total,
            "average_files_generated": round(avg_files, 1),
            "most_common_errors": sorted(common_errors.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    def get_last_project(self) -> Dict[str, Any]:
        """Retorna el último proyecto registrado."""
        projects = self._data.get("projects", [])
        return projects[-1] if projects else {}