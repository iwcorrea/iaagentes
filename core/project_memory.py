"""
Memoria estructurada del proyecto.
Extiende ProjectState con consultas rápidas, hashes de contenido,
issues de auditoría, resúmenes contextuales y gestión documental.
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.document_manager import DocumentManager


class ProjectMemory:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.state_file = self.workspace_path / "project_state.json"
        self._data = self._load()
        # Gestor documental
        docs_folder = self.workspace_path / "docs"
        self.docs = DocumentManager(docs_folder)

    def _load(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding='utf-8'))
            except:
                pass
        return {
            "created_at": datetime.now().isoformat(),
            "phases_completed": [],
            "files_manifest": [],
            "errors": [],
            "last_prompt": "",
            "model_used": "",
            "dependencies_cached": False,
            "tests_generated": False,
            "deploy_files_generated": False,
            "design_decisions": [],
            "audit_issues": [],
            "change_log": []
        }

    def _save(self):
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding='utf-8')

    # -----------------------------------------------------------------
    # Fases
    # -----------------------------------------------------------------
    def mark_phase_completed(self, phase_name: str):
        if phase_name not in self._data["phases_completed"]:
            self._data["phases_completed"].append(phase_name)
        self._save()

    def is_phase_completed(self, phase_name: str) -> bool:
        return phase_name in self._data["phases_completed"]

    # -----------------------------------------------------------------
    # Manifiesto de archivos con hash
    # -----------------------------------------------------------------
    def add_file(self, file_path: str, content: str, description: str = ""):
        full_path = self.workspace_path / file_path
        size = len(content)
        content_hash = hashlib.md5(content.encode()).hexdigest()
        for entry in self._data["files_manifest"]:
            if entry["path"] == file_path:
                entry["size"] = size
                entry["hash"] = content_hash
                entry["description"] = description or entry.get("description", "")
                self._save()
                return
        self._data["files_manifest"].append({
            "path": file_path,
            "size": size,
            "hash": content_hash,
            "description": description
        })
        self._data["change_log"].append({
            "timestamp": datetime.now().isoformat(),
            "action": "created",
            "file": file_path
        })
        self._save()

    def file_exists(self, file_path: str) -> bool:
        return any(f["path"] == file_path for f in self._data["files_manifest"])

    def get_file_hash(self, file_path: str) -> Optional[str]:
        for f in self._data["files_manifest"]:
            if f["path"] == file_path:
                return f.get("hash")
        return None

    def get_files_by_extension(self, ext: str) -> List[str]:
        return [f["path"] for f in self._data["files_manifest"] if f["path"].endswith(ext)]

    def get_manifest_summary(self) -> str:
        if not self._data["files_manifest"]:
            return "📁 Proyecto vacío."
        lines = ["📁 Archivos existentes:"]
        for f in self._data["files_manifest"]:
            lines.append(f"  - {f['path']} ({f.get('description', '')})")
        return "\n".join(lines)

    # -----------------------------------------------------------------
    # Decisiones de diseño
    # -----------------------------------------------------------------
    def add_design_decision(self, decision: str):
        self._data["design_decisions"].append({
            "timestamp": datetime.now().isoformat(),
            "decision": decision
        })
        self._save()

    def get_design_context(self) -> str:
        if not self._data["design_decisions"]:
            return ""
        return "📐 Decisiones de diseño:\n" + "\n".join(
            f"  - {d['decision']}" for d in self._data["design_decisions"]
        )

    # -----------------------------------------------------------------
    # Issues de auditoría
    # -----------------------------------------------------------------
    def add_audit_issue(self, file: str, line: int, message: str, severity: str = "warning"):
        self._data["audit_issues"].append({
            "file": file,
            "line": line,
            "message": message,
            "severity": severity,
            "fixed": False
        })
        self._save()

    def get_pending_issues(self) -> List[Dict]:
        return [i for i in self._data["audit_issues"] if not i.get("fixed", False)]

    def mark_issue_fixed(self, index: int):
        if 0 <= index < len(self._data["audit_issues"]):
            self._data["audit_issues"][index]["fixed"] = True
            self._save()

    # -----------------------------------------------------------------
    # Errores y prompt
    # -----------------------------------------------------------------
    def add_error(self, error: str):
        self._data["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "message": error
        })
        self._save()

    def set_last_prompt(self, prompt: str):
        self._data["last_prompt"] = prompt
        self._save()

    def set_model_used(self, model: str):
        self._data["model_used"] = model
        self._save()

    # -----------------------------------------------------------------
    # Flags
    # -----------------------------------------------------------------
    def set_dependencies_cached(self, value=True):
        self._data["dependencies_cached"] = value
        self._save()

    def set_tests_generated(self, value=True):
        self._data["tests_generated"] = value
        self._save()

    def set_deploy_generated(self, value=True):
        self._data["deploy_files_generated"] = value
        self._save()

    # -----------------------------------------------------------------
    # Utilidades para agentes (consultas rápidas)
    # -----------------------------------------------------------------
    def get_models(self) -> List[str]:
        models = []
        for f in self._data["files_manifest"]:
            if "models/" in f["path"] and f["path"].endswith(".py"):
                models.append(Path(f["path"]).stem)
        return models

    def get_routers(self) -> List[str]:
        routers = []
        for f in self._data["files_manifest"]:
            if ("routers/" in f["path"] or "routes/" in f["path"]) and f["path"].endswith(".py"):
                routers.append(Path(f["path"]).stem)
        return routers

    # -----------------------------------------------------------------
    # NUEVO: acceso a documentos
    # -----------------------------------------------------------------
    def get_instructions_for_agent(self, agent_role: str) -> str:
        """Obtiene las instrucciones relevantes para un agente específico."""
        return self.docs.get_context_for_agent(agent_role)

    def get_all_instructions(self) -> str:
        return self.docs.get_all_instructions()

    def to_dict(self) -> Dict:
        return dict(self._data)