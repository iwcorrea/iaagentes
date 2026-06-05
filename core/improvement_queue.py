import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class ImprovementQueue:
    """
    Cola persistente de propuestas de mejora.
    Almacena las sugerencias en un archivo JSON en workspace/.
    """

    def __init__(self, storage_path: str = "workspace/improvements.json"):
        self.storage_path = Path(storage_path)
        self._ensure_storage()

    def _ensure_storage(self):
        if not self.storage_path.exists():
            self.storage_path.write_text(json.dumps([], indent=2))

    def _load(self) -> List[Dict]:
        try:
            return json.loads(self.storage_path.read_text())
        except:
            return []

    def _save(self, data: List[Dict]):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(data, indent=2))

    def add_proposal(self, agent_name: str, title: str, description: str,
                     target_file: str, suggested_code: str = "",
                     reason: str = "") -> str:
        """Añade una nueva propuesta y devuelve su ID."""
        proposals = self._load()
        proposal_id = str(uuid.uuid4())[:8]
        proposal = {
            "id": proposal_id,
            "agent": agent_name,
            "title": title,
            "description": description,
            "target_file": target_file,
            "suggested_code": suggested_code,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "applied_at": None,
            "result": None
        }
        proposals.append(proposal)
        self._save(proposals)
        return proposal_id

    def list_pending(self) -> List[Dict]:
        """Devuelve propuestas pendientes de revisión."""
        return [p for p in self._load() if p["status"] == "pending"]

    def list_all(self) -> List[Dict]:
        return self._load()

    def get_proposal(self, proposal_id: str) -> Optional[Dict]:
        for p in self._load():
            if p["id"] == proposal_id:
                return p
        return None

    def approve(self, proposal_id: str) -> Optional[Dict]:
        """Aprueba una propuesta y devuelve sus datos para aplicar."""
        proposals = self._load()
        for p in proposals:
            if p["id"] == proposal_id and p["status"] == "pending":
                p["status"] = "approved"
                p["applied_at"] = datetime.now().isoformat()
                self._save(proposals)
                return p
        return None

    def reject(self, proposal_id: str) -> bool:
        proposals = self._load()
        for p in proposals:
            if p["id"] == proposal_id and p["status"] == "pending":
                p["status"] = "rejected"
                self._save(proposals)
                return True
        return False

    def mark_applied(self, proposal_id: str, result: str = ""):
        proposals = self._load()
        for p in proposals:
            if p["id"] == proposal_id:
                p["status"] = "applied"
                p["result"] = result
                self._save(proposals)
                return True
        return False