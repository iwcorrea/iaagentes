import json
import re
from typing import Dict, List, Any

class PlanValidator:
    """
    Valida que un plan JSON cubra todos los requisitos del prompt del usuario
    y que la arquitectura propuesta sea coherente y completa.
    """

    # Archivos mínimos esperados por tipo de proyecto
    MINIMAL_FILES = {
        "fastapi": [
            "backend/main.py",
            "backend/database.py",
            "backend/models.py",
            "backend/schemas.py",
            "backend/auth.py",
            "backend/requirements.txt"
        ],
        "react": [
            "frontend/package.json",
            "frontend/src/App.jsx",
            "frontend/src/index.jsx"
        ]
    }

    def validate(self, plan: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """
        Retorna un dict con:
        - valid: bool
        - missing_files: list[str]
        - extra_files: list[str]
        - suggestions: list[str]
        """
        result = {
            "valid": True,
            "missing_files": [],
            "extra_files": [],
            "suggestions": []
        }

        # 1. Extraer keywords del prompt
        prompt_lower = user_prompt.lower()
        requires_backend = any(word in prompt_lower for word in [
            "fastapi", "backend", "api", "rest", "graphql", "endpoint", "base de datos"
        ])
        requires_frontend = any(word in prompt_lower for word in [
            "react", "frontend", "interfaz", "ui", "página", "web", "tailwind", "html"
        ])
        requires_auth = any(word in prompt_lower for word in [
            "login", "registro", "jwt", "auth", "autenticación", "usuario", "roles"
        ])

        # 2. Construir conjunto de archivos esperados
        expected_files = set()
        if requires_backend:
            expected_files.update(self.MINIMAL_FILES["fastapi"])
        if requires_frontend:
            expected_files.update(self.MINIMAL_FILES["react"])

        # Añadir archivos específicos según keywords
        if requires_auth and requires_backend:
            expected_files.add("backend/routers/auth.py")

        # Archivos declarados en el plan
        planned_files = set()
        if "files" in plan:
            for file_info in plan["files"]:
                path = file_info.get("path", "")
                planned_files.add(path)

        # 3. Detectar faltantes
        missing = expected_files - planned_files
        if missing:
            result["valid"] = False
            result["missing_files"] = sorted(list(missing))
            result["suggestions"].append(f"Faltan archivos esenciales: {', '.join(sorted(missing))}")

        # 4. Detectar archivos posiblemente innecesarios
        # (archivos planeados que no están en los esperados y no parecen justificados)
        # Esto es heurístico y puede mejorarse
        if len(planned_files) > len(expected_files) * 1.5:
            extra = planned_files - expected_files
            result["extra_files"] = sorted(list(extra))
            result["suggestions"].append(f"Revisar si estos archivos son necesarios: {', '.join(sorted(extra))}")

        # 5. Verificar coherencia: si hay routers, debe haber modelos y schemas
        has_routers = any("routers/" in f for f in planned_files)
        if has_routers:
            if "backend/models.py" not in planned_files:
                result["valid"] = False
                result["missing_files"].append("backend/models.py")
                result["suggestions"].append("Los routers requieren modelos de datos (models.py)")
            if "backend/schemas.py" not in planned_files:
                result["valid"] = False
                result["missing_files"].append("backend/schemas.py")
                result["suggestions"].append("Los routers requieren schemas Pydantic (schemas.py)")

        return result