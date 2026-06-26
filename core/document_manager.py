"""
Gestor de documentos Markdown con frontmatter para guiar a los agentes.
Soporta filtrado por agente, prioridad y tags.
"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional

class DocumentManager:
    def __init__(self, docs_path: Path):
        self.docs_path = docs_path
        self._cache: Dict[str, dict] = {}
        self._load_all()

    def _load_all(self):
        if not self.docs_path.exists():
            return
        for md_file in self.docs_path.glob("*.md"):
            self._load_file(md_file)

    def _load_file(self, file_path: Path):
        content = file_path.read_text(encoding='utf-8')
        metadata, body = self._parse_frontmatter(content)
        self._cache[file_path.stem] = {
            "path": str(file_path),
            "metadata": metadata,
            "body": body
        }

    def _parse_frontmatter(self, text: str):
        """Extrae frontmatter YAML del inicio del documento."""
        if text.startswith('---'):
            parts = text.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    metadata = {}
                body = parts[2].strip()
                return metadata, body
        return {}, text.strip()

    def get_context_for_agent(self, agent_role: str) -> str:
        """Devuelve las instrucciones relevantes para un rol de agente específico."""
        applicable = []
        for doc_name, doc in self._cache.items():
            target = doc["metadata"].get("target_agents", [])
            # Si target está vacío, se considera aplicable a todos
            if not target or agent_role in target:
                applicable.append(doc)
        # Ordenar por prioridad (high primero)
        applicable.sort(key=lambda d: 0 if d["metadata"].get("priority") == "high" else 1)
        if not applicable:
            return ""
        lines = ["📚 **Instrucciones del proyecto:**"]
        for doc in applicable:
            lines.append(f"### {Path(doc['path']).stem}")
            lines.append(doc["body"])
            lines.append("")
        return "\n".join(lines)

    def get_all_instructions(self) -> str:
        """Devuelve todas las instrucciones juntas."""
        if not self._cache:
            return ""
        lines = ["📚 **Documentos del proyecto:**"]
        for doc_name, doc in self._cache.items():
            lines.append(f"### {Path(doc['path']).stem}")
            lines.append(doc["body"])
            lines.append("")
        return "\n".join(lines)

    def get_document_by_tag(self, tag: str) -> Optional[str]:
        for doc in self._cache.values():
            if tag in doc["metadata"].get("tags", []):
                return doc["body"]
        return None