import re
from typing import Dict, Any

class PromptIntegrity:
    """Valida la claridad y coherencia del prompt antes de enviarlo a los agentes."""

    AMBIGUOUS_TERMS = {
        "app": "Si deseás una app móvil, especificá 'app móvil' o 'React Native'. Si es web, usá 'página web' o 'React'.",
        "sistema": "Detallá si es una API, un frontend web o una app de escritorio.",
        "dashboard": "Indicá si es un panel de administración web o una app móvil.",
        "frontend": "Especificá el framework: React, Vue, Svelte, etc.",
        "backend": "Especificá el framework: FastAPI, Django, Flask, etc.",
        "base de datos": "Indicá si querés SQLite, PostgreSQL, MySQL, etc.",
        "login": "Asegurate de mencionar si necesitás autenticación JWT o sesiones.",
    }

    def validate(self, prompt: str) -> Dict[str, Any]:
        result = {
            "valid": True,
            "warnings": [],
            "suggestions": [],
            "detected_types": [],
        }

        lower = prompt.lower()

        # Detectar tipo de proyecto
        if any(word in lower for word in ["web", "página", "frontend", "react", "vue", "svelte"]):
            result["detected_types"].append("web_app")
        if any(word in lower for word in ["móvil", "app móvil", "react native", "expo", "celular", "android", "ios"]):
            result["detected_types"].append("mobile_app")
        if any(word in lower for word in ["api", "rest", "graphql", "endpoint", "microservicio"]):
            result["detected_types"].append("api")
        if any(word in lower for word in ["landing", "página de aterrizaje", "sitio estático"]):
            result["detected_types"].append("landing_page")

        if not result["detected_types"]:
            result["warnings"].append("No se pudo determinar el tipo de proyecto. Especificá 'app web', 'API', 'app móvil', etc.")
            result["valid"] = False

        # Detectar ambigüedades
        for term, suggestion in self.AMBIGUOUS_TERMS.items():
            if term in lower:
                # Si la palabra aparece pero no hay detalles adicionales
                if term == "app" and "web" not in lower and "móvil" not in lower and "mobile" not in lower:
                    result["warnings"].append(f"'{term}' es ambiguo. {suggestion}")
                    result["valid"] = False
                elif term == "frontend" and not any(f in lower for f in ["react", "vue", "svelte", "angular"]):
                    result["suggestions"].append(suggestion)
                elif term == "backend" and not any(b in lower for b in ["fastapi", "django", "flask"]):
                    result["suggestions"].append(suggestion)
                elif term == "login" and not any(a in lower for a in ["jwt", "auth", "autenticación"]):
                    result["suggestions"].append(suggestion)

        # Verificar longitud mínima
        if len(prompt.split()) < 5:
            result["warnings"].append("El prompt es muy corto. Agregá más detalles para obtener un proyecto completo.")
            result["valid"] = False

        return result

    def build_improved_prompt(self, prompt: str) -> str:
        """Sugiere un prompt mejorado basado en las advertencias encontradas."""
        validation = self.validate(prompt)
        if validation["valid"] and not validation["suggestions"]:
            return prompt

        improved = prompt.strip()
        if validation["suggestions"]:
            improved += "\n\nSugerencias automáticas para mejorar el resultado:\n"
            for s in validation["suggestions"]:
                improved += f"- {s}\n"

        return improved