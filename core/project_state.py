"""
Persistencia del estado del proyecto.
Guarda fases completadas, archivos generados con metadata (manifiesto),
errores, último prompt y flags de progreso. Sirve para reanudar
generaciones interrumpidas y para inyectar contexto en los agentes.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class ProjectState:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.state_file = self.workspace_path / "project_state.json"
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "created_at": datetime.now().isoformat(),
            "phases_completed": [],
            "files_manifest": [],         # lista de dicts con path, size, description
            "errors": [],
            "last_prompt": "",
            "model_used": "",
            "dependencies_cached": False,
            "tests_generated": False,
            "deploy_files_generated": False,
        }

    def _save(self):
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding='utf-8')

    # ------------------------------------------------------------------
    # Fases
    # ------------------------------------------------------------------
    def mark_phase_completed(self, phase_name: str):
        if phase_name not in self._data["phases_completed"]:
            self._data["phases_completed"].append(phase_name)
        self._save()

    def is_phase_completed(self, phase_name: str) -> bool:
        return phase_name in self._data["phases_completed"]

    # ------------------------------------------------------------------
    # Manifiesto de archivos (anti‑alucinación + ahorro de tokens)
    # ------------------------------------------------------------------
    def add_file_manifest_entry(self, file_path: str, description: str = "", size: int = None):
        """Agrega o actualiza la metadata de un archivo generado."""
        # Determinar tamaño si no se pasa
        if size is None:
            full_path = self.workspace_path / file_path
            if full_path.exists():
                size = full_path.stat().st_size
            else:
                size = 0

        # Buscar si ya existe
        for entry in self._data["files_manifest"]:
            if entry["path"] == file_path:
                entry["size"] = size
                entry["description"] = description
                self._save()
                return

        # Nuevo registro
        self._data["files_manifest"].append({
            "path": file_path,
            "size": size,
            "description": description
        })
        self._save()

    def remove_file_from_manifest(self, file_path: str):
        self._data["files_manifest"] = [
            e for e in self._data["files_manifest"] if e["path"] != file_path
        ]
        self._save()

    def get_files_manifest(self) -> List[Dict[str, Any]]:
        return list(self._data["files_manifest"])

    def get_manifest_as_context(self) -> str:
        """
        Devuelve un texto resumido para incluir en los prompts,
        indicando qué archivos existen y una breve descripción.
        Así los agentes no alucinan con archivos inexistentes.
        """
        if not self._data["files_manifest"]:
            return "📁 El proyecto está vacío."

        lines = ["📁 Archivos existentes en el proyecto:"]
        for f in self._data["files_manifest"]:
            size_kb = f["size"] / 1024 if f["size"] else 0
            desc = f["description"] or "sin descripción"
            lines.append(f"  - {f['path']} ({size_kb:.1f} KB) – {desc}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Errores
    # ------------------------------------------------------------------
    def add_error(self, error: str):
        self._data["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "message": error
        })
        self._save()

    # ------------------------------------------------------------------
    # Prompt y modelo
    # ------------------------------------------------------------------
    def set_last_prompt(self, prompt: str):
        self._data["last_prompt"] = prompt
        self._save()

    def set_model_used(self, model: str):
        self._data["model_used"] = model
        self._save()

    # ------------------------------------------------------------------
    # Flags de progreso
    # ------------------------------------------------------------------
    def set_dependencies_cached(self, value: bool = True):
        self._data["dependencies_cached"] = value
        self._save()

    def set_tests_generated(self, value: bool = True):
        self._data["tests_generated"] = value
        self._save()

    def set_deploy_generated(self, value: bool = True):
        self._data["deploy_files_generated"] = value
        self._save()

    # ------------------------------------------------------------------
    # Resumen para endpoints
    # ------------------------------------------------------------------
    def get_summary(self) -> Dict[str, Any]:
        return {
            "phases_completed": len(self._data["phases_completed"]),
            "files_generated": len(self._data["files_manifest"]),
            "errors": len(self._data["errors"]),
            "can_resume": len(self._data["phases_completed"]) > 0,
            "last_prompt": self._data["last_prompt"][:100] if self._data["last_prompt"] else "",
        }

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)