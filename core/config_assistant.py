"""
Asistente de Configuración Guiada para Proyectos.
Genera preguntas profesionales según el tipo de proyecto y
construye un prompt detallado para los agentes.
"""
from typing import Dict, List, Any

class ConfigAssistant:
    def __init__(self):
        self.schemas = {
            "web_app": {
                "name": "Aplicación Web Full-Stack",
                "description": "Backend + Frontend en una sola aplicación",
                "questions": [
                    {"id": "project_name", "question": "¿Nombre del proyecto?", "type": "text", "default": "MiApp"},
                    {"id": "auth_required", "question": "¿Necesita autenticación de usuarios?", "type": "boolean", "default": True},
                    {"id": "user_roles", "question": "¿Roles de usuario? (admin, cliente, etc.)", "type": "text", "default": "admin, cliente", "condition": "auth_required"},
                    {"id": "database", "question": "¿Tipo de base de datos?", "type": "choice", "options": ["sqlite", "postgresql", "mysql"], "default": "sqlite"},
                    {"id": "frontend_framework", "question": "¿Framework Frontend?", "type": "choice", "options": ["react", "vue", "svelte"], "default": "react"},
                    {"id": "css_framework", "question": "¿Framework CSS?", "type": "choice", "options": ["tailwind", "bootstrap", "none"], "default": "tailwind"},
                    {"id": "deploy_target", "question": "¿Plataforma de despliegue?", "type": "choice", "options": ["vercel", "netlify", "docker", "none"], "default": "docker"},
                    {"id": "additional_features", "question": "¿Características adicionales? (api rest, dashboard, reportes, notificaciones)", "type": "text", "default": "api rest, dashboard"},
                ]
            },
            "mobile_app": {
                "name": "Aplicación Móvil (PWA/React Native)",
                "description": "Aplicación para dispositivos móviles",
                "questions": [
                    {"id": "project_name", "question": "¿Nombre de la app?", "type": "text", "default": "MiAppMovil"},
                    {"id": "auth_required", "question": "¿Necesita autenticación?", "type": "boolean", "default": True},
                    {"id": "backend_api", "question": "¿Incluir backend API?", "type": "boolean", "default": True},
                    {"id": "database", "question": "¿Base de datos para el backend?", "type": "choice", "options": ["sqlite", "postgresql", "firebase"], "default": "sqlite", "condition": "backend_api"},
                    {"id": "offline_mode", "question": "¿Soporte offline?", "type": "boolean", "default": True},
                    {"id": "push_notifications", "question": "¿Notificaciones push?", "type": "boolean", "default": False},
                ]
            },
            "api_rest": {
                "name": "API REST",
                "description": "Solo backend, sin frontend",
                "questions": [
                    {"id": "project_name", "question": "¿Nombre de la API?", "type": "text", "default": "MiAPI"},
                    {"id": "auth_required", "question": "¿Autenticación JWT?", "type": "boolean", "default": True},
                    {"id": "database", "question": "¿Base de datos?", "type": "choice", "options": ["sqlite", "postgresql", "mongodb"], "default": "sqlite"},
                    {"id": "orm", "question": "¿ORM?", "type": "choice", "options": ["sqlalchemy", "prisma", "tortoise"], "default": "sqlalchemy"},
                    {"id": "versioning", "question": "¿Versionado de API? (v1, v2)", "type": "boolean", "default": True},
                ]
            },
            "landing_page": {
                "name": "Landing Page",
                "description": "Página de aterrizaje o sitio web estático",
                "questions": [
                    {"id": "project_name", "question": "¿Nombre del sitio?", "type": "text", "default": "MiLanding"},
                    {"id": "sections", "question": "¿Secciones? (hero, features, pricing, contact, footer)", "type": "text", "default": "hero, features, contact, footer"},
                    {"id": "css_framework", "question": "¿Framework CSS?", "type": "choice", "options": ["tailwind", "bootstrap", "pure-css"], "default": "tailwind"},
                    {"id": "animations", "question": "¿Incluir animaciones?", "type": "boolean", "default": True},
                ]
            }
        }

    def get_project_types(self) -> List[Dict]:
        return [
            {"id": key, "name": val["name"], "description": val["description"]}
            for key, val in self.schemas.items()
        ]

    def get_questions(self, project_type: str) -> List[Dict]:
        schema = self.schemas.get(project_type)
        if not schema:
            return []
        return schema["questions"]

    def build_prompt(self, project_type: str, answers: Dict[str, Any]) -> str:
        schema = self.schemas.get(project_type)
        if not schema:
            return "Tipo de proyecto no válido."

        project_name = answers.get("project_name", "Proyecto")

        lines = [
            f"Crea un proyecto de tipo {schema['name']} llamado {project_name}.",
            ""
        ]

        for question in schema["questions"]:
            q_id = question["id"]
            if q_id in answers and answers[q_id] is not None and answers[q_id] != "":
                value = answers[q_id]
                if isinstance(value, bool):
                    if value:
                        lines.append(f"- Incluir: {question['question'].replace('¿', '').replace('?', '').strip()}")
                else:
                    lines.append(f"- {question['question'].replace('¿', '').replace('?', '').strip()}: {value}")

        lines.append("")
        lines.append("Reglas adicionales:")
        lines.append("- Genera todos los archivos necesarios (backend, frontend, configuración).")
        lines.append("- Incluye requirements.txt y package.json.")
        lines.append("- Usa variables de entorno para secretos.")
        lines.append("- El código debe ser funcional y listo para ejecutar.")

        return "\n".join(lines)