"""
Caché inteligente de dependencias.
Aprende de proyectos anteriores para no repetir llamadas al LLM.
Guarda el mapeo import → paquete en un archivo JSON.
"""
import json
from pathlib import Path
from typing import Dict, Optional

CACHE_FILE = Path("dependency_cache.json")

# Mapeo base de imports comunes a paquetes (conocimiento inicial)
BASE_MAP = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "sqlalchemy": "sqlalchemy",
    "sqlmodel": "sqlmodel",
    "pydantic": "pydantic",
    "jose": "python-jose",
    "jwt": "python-jose",
    "passlib": "passlib",
    "bcrypt": "bcrypt",
    "hashlib": "hashlib",       # built-in, pero lo dejamos para evitar llamadas
    "secrets": "secrets",        # built-in
    "starlette": "starlette",
    "httpx": "httpx",
    "requests": "requests",
    "dotenv": "python-dotenv",
    "yaml": "pyyaml",
    "networkx": "networkx",
    "alembic": "alembic",
    "structlog": "structlog",
    "web3": "web3",
    "pytest": "pytest",
    "multipart": "python-multipart",
    "react": "react",
    "react-dom": "react-dom",
    "react-router-dom": "react-router-dom",
    "axios": "axios",
    "vite": "vite",
    "tailwindcss": "tailwindcss",
    "postcss": "postcss",
    "autoprefixer": "autoprefixer",
    "recharts": "recharts",
    "lucide-react": "lucide-react",
    "@tanstack/react-query": "@tanstack/react-query",
}


class DependencyCache:
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._load()

    def _load(self):
        """Carga la caché desde el archivo JSON, o crea una nueva con el mapeo base."""
        if CACHE_FILE.exists():
            try:
                self._cache = json.loads(CACHE_FILE.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError):
                self._cache = {}
        else:
            self._cache = dict(BASE_MAP)
            self._save()

    def _save(self):
        """Guarda la caché en disco."""
        CACHE_FILE.write_text(json.dumps(self._cache, indent=2), encoding='utf-8')

    def get(self, import_name: str) -> Optional[str]:
        """Retorna el paquete asociado al import, o None si no está en caché."""
        return self._cache.get(import_name)

    def add(self, import_name: str, package_name: str):
        """Agrega una nueva asociación import → paquete y la persiste."""
        self._cache[import_name] = package_name
        self._save()

    def get_all(self) -> Dict[str, str]:
        """Retorna todo el diccionario de caché."""
        return dict(self._cache)

    def has(self, import_name: str) -> bool:
        """Verifica si un import ya está en caché."""
        return import_name in self._cache

    def stats(self) -> dict:
        """Estadísticas de la caché."""
        return {
            "total_entries": len(self._cache),
            "base_entries": len(BASE_MAP),
            "learned_entries": len(self._cache) - len(BASE_MAP),
        }