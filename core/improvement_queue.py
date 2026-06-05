"""
Cola de mejoras para el ecosistema autónomo.
Los agentes y el MetaAgent pueden proponer mejoras que quedan
pendientes de revisión, aprobación o rechazo.
"""

import json
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class ImprovementQueue:
    """
    Gestiona propuestas de mejora del ecosistema.
    Las almacena en un archivo JSON para persistencia.
    """

    def __init__(self, storage_path: str = "workspace/improvements.json"):
        self.storage_path = Path(storage_path).resolve()
        self._ensure_storage()

    def _ensure_storage(self):
        """Crea el archivo de almacenamiento si no existe."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text(json.dumps([], indent=2))

    def _read_all(self) -> List[Dict[str, Any]]:
        """Lee todas las propuestas del archivo."""
        try:
            return json.loads(self.storage_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_all(self, proposals: List[Dict[str, Any]]):
        """Escribe todas las propuestas al archivo."""
        self.storage_path.write_text(json.dumps(proposals, indent=2))

    def add_proposal(
        self,
        agent_name: str,
        title: str,
        description: str,
        target_file: str,
        suggested_code: str = "",
        reason: str = ""
    ) -> str:
        """
        Añade una nueva propuesta de mejora.
        Retorna el ID de la propuesta.
        """
        proposal_id = uuid.uuid4().hex[:8]
        proposal = {
            "id": proposal_id,
            "agent_name": agent_name,
            "title": title,
            "description": description,
            "target_file": target_file,
            "suggested_code": suggested_code,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "applied_at": None,
            "result_message": None
        }
        proposals = self._read_all()
        proposals.append(proposal)
        self._write_all(proposals)
        return proposal_id

    def approve(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Aprueba una propuesta (cambia su estado a 'approved')."""
        proposals = self._read_all()
        for p in proposals:
            if p["id"] == proposal_id and p["status"] == "pending":
                p["status"] = "approved"
                self._write_all(proposals)
                return p
        return None

    def reject(self, proposal_id: str) -> bool:
        """Rechaza una propuesta (cambia su estado a 'rejected')."""
        proposals = self._read_all()
        for p in proposals:
            if p["id"] == proposal_id and p["status"] == "pending":
                p["status"] = "rejected"
                self._write_all(proposals)
                return True
        return False

    def mark_applied(self, proposal_id: str, message: str = ""):
        """Marca una propuesta como aplicada."""
        proposals = self._read_all()
        for p in proposals:
            if p["id"] == proposal_id:
                p["status"] = "applied"
                p["applied_at"] = datetime.now().isoformat()
                p["result_message"] = message
                self._write_all(proposals)
                return True
        return False

    def list_pending(self) -> List[Dict[str, Any]]:
        """Lista todas las propuestas pendientes."""
        proposals = self._read_all()
        return [p for p in proposals if p["status"] == "pending"]

    def list_all(self) -> List[Dict[str, Any]]:
        """Lista todas las propuestas."""
        return self._read_all()

    def get_by_id(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una propuesta por su ID."""
        proposals = self._read_all()
        for p in proposals:
            if p["id"] == proposal_id:
                return p
        return None