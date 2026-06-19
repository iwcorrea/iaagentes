"""
Contexto de proyecto en memoria.
Evita leer archivos repetidamente durante la generación.
"""
from pathlib import Path
from typing import Dict, Optional

class ProjectContext:
    def __init__(self):
        self._cache: Dict[str, str] = {}

    def read_file(self, workspace: Path, relative_path: str) -> Optional[str]:
        full_path = workspace / relative_path
        cache_key = str(full_path)
        if cache_key in self._cache:
            return self._cache[cache_key]
        if full_path.exists():
            try:
                content = full_path.read_text(encoding='utf-8')
                self._cache[cache_key] = content
                return content
            except:
                pass
        return None

    def clear(self):
        self._cache.clear()