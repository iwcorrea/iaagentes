from typing import Dict, List, Any, Optional
from core.prompt_integrity import PromptIntegrity

TEMPLATES = {
    "web_app": {
        "name": "App Web Full‑Stack",
        "description": "Backend FastAPI + Frontend React con Tailwind. Autenticación JWT, base de datos SQLite, estructura profesional lista para producción.",
        "files_generated": [
            "backend/main.py", "backend/models.py", "backend/schemas.py", "backend/auth.py",
            "backend/database.py", "backend/requirements.txt",
            "frontend/package.json", "frontend/vite.config.js", "frontend/tailwind.config.js",
            "frontend/postcss.config.js", "frontend/index.html",
            "frontend/src/main.jsx", "frontend/src/App.jsx", "frontend/src/index.css",
            "frontend/src/components/Login.jsx", "frontend/src/components/Dashboard.jsx",
            "Dockerfile", ".env.example"
        ],
        "questions": [
            {"id": "project_name", "question": "¿Nombre del proyecto?", "type": "text", "default": "MiApp"},
            {"id": "auth_required", "question": "¿Necesita autenticación de usuarios?", "type": "boolean", "default": True},
            {"id": "user_roles", "question": "¿Roles de usuario? (admin, cliente, etc.)", "type": "text", "default": "admin, cliente", "condition": "auth_required"},
            {"id": "database", "question": "¿Tipo de base de datos?", "type": "choice", "options": ["sqlite", "postgresql", "mysql"], "default": "sqlite"},
            {"id": "frontend_framework", "question": "¿Framework Frontend?", "type": "choice", "options": ["react", "vue", "svelte"], "default": "react"},
            {"id": "css_framework", "question": "¿Framework CSS?", "type": "choice", "options": ["tailwind", "bootstrap", "none"], "default": "tailwind"},
            {"id": "deploy_target", "question": "¿Plataforma de despliegue?", "type": "choice", "options": ["vercel", "netlify", "docker", "none"], "default": "docker"},
            {"id": "features", "question": "¿Características adicionales? (dashboard, reportes, notificaciones, api rest)", "type": "text", "default": "dashboard, api rest"},
        ]
    },
    "ecommerce": {
        "name": "E‑Commerce",
        "description": "Tienda online con catálogo de productos, carrito de compras, autenticación y panel de administración.",
        "files_generated": [
            "backend/main.py", "backend/models.py", "backend/schemas.py", "backend/auth.py",
            "backend/database.py", "backend/requirements.txt",
            "backend/routers/products.py", "backend/routers/cart.py", "backend/routers/orders.py",
            "frontend/package.json", "frontend/src/App.jsx", "frontend/src/components/ProductList.jsx",
            "frontend/src/components/Cart.jsx", "frontend/src/components/Checkout.jsx",
            "Dockerfile", ".env.example"
        ],
        "questions": [
            {"id": "project_name", "question": "¿Nombre de la tienda?", "type": "text", "default": "MiTienda"},
            {"id": "auth_required", "question": "¿Autenticación de usuarios?", "type": "boolean", "default": True},
            {"id": "payment_method", "question": "¿Método de pago?", "type": "choice", "options": ["stripe", "paypal", "simulado"], "default": "simulado"},
            {"id": "database", "question": "¿Base de datos?", "type": "choice", "options": ["sqlite", "postgresql"], "default": "postgresql"},
            {"id": "admin_panel", "question": "¿Panel de administración?", "type": "boolean", "default": True},
        ]
    },
    "api_rest": {
        "name": "API REST",
        "description": "Backend puro sin frontend. Ideal para microservicios o integraciones.",
        "files_generated": [
            "backend/main.py", "backend/models.py", "backend/schemas.py", "backend/auth.py",
            "backend/database.py", "backend/requirements.txt",
            "Dockerfile", ".env.example", "tests/test_api.py"
        ],
        "questions": [
            {"id": "project_name", "question": "¿Nombre de la API?", "type": "text", "default": "MiAPI"},
            {"id": "auth_required", "question": "¿Autenticación JWT?", "type": "boolean", "default": True},
            {"id": "database", "question": "¿Base de datos?", "type": "choice", "options": ["sqlite", "postgresql", "mongodb"], "default": "sqlite"},
            {"id": "versioning", "question": "¿Versionado de API? (v1, v2)", "type": "boolean", "default": True},
        ]
    },
    "dashboard": {
        "name": "Panel de Administración",
        "description": "Dashboard con métricas, gráficos, gestión de usuarios y roles.",
        "files_generated": [
            "backend/main.py", "backend/models.py", "backend/schemas.py", "backend/auth.py",
            "backend/database.py", "backend/requirements.txt",
            "frontend/package.json", "frontend/src/App.jsx", "frontend/src/components/Dashboard.jsx",
            "frontend/src/components/UserManagement.jsx", "frontend/src/components/Charts.jsx",
            "Dockerfile", ".env.example"
        ],
        "questions": [
            {"id": "project_name", "question": "¿Nombre del panel?", "type": "text", "default": "AdminPanel"},
            {"id": "auth_required", "question": "¿Autenticación?", "type": "boolean", "default": True},
            {"id": "roles", "question": "¿Roles? (admin, editor, viewer)", "type": "text", "default": "admin, editor, viewer"},
            {"id": "charts", "question": "¿Gráficos y estadísticas?", "type": "boolean", "default": True},
        ]
    },
    "landing_page": {
        "name": "Landing Page",
        "description": "Página de aterrizaje o sitio web estático con diseño moderno.",
        "files_generated": [
            "frontend/index.html", "frontend/src/App.jsx", "frontend/src/index.css",
            "frontend/package.json", "frontend/vite.config.js", "frontend/tailwind.config.js"
        ],
        "questions": [
            {"id": "project_name", "question": "¿Nombre del sitio?", "type": "text", "default": "MiLanding"},
            {"id": "sections", "question": "¿Secciones? (hero, features, pricing, contact, footer)", "type": "text", "default": "hero, features, contact, footer"},
            {"id": "animations", "question": "¿Incluir animaciones?", "type": "boolean", "default": True},
        ]
    }
}

class GuidedBuilder:
    def __init__(self):
        self.validator = PromptIntegrity()

    def get_templates(self) -> List[Dict]:
        return [{"id": k, "name": v["name"], "description": v["description"], "files_generated": v["files_generated"]} for k, v in TEMPLATES.items()]

    def get_questions(self, template_id: str) -> Optional[List[Dict]]:
        template = TEMPLATES.get(template_id)
        return template["questions"] if template else None

    def preview_prompt(self, template_id: str, answers: Dict[str, Any]) -> str:
        template = TEMPLATES.get(template_id)
        if not template:
            return "Tipo de proyecto no válido."
        prompt = self._build_prompt(template_id, answers)
        # Validación gratuita
        validation = self.validator.validate(prompt)
        if not validation["valid"]:
            prompt = self.validator.build_improved_prompt(prompt)
        return prompt

    def validate_and_build(self, template_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        template = TEMPLATES.get(template_id)
        if not template:
            return {"error": "Tipo de proyecto no válido."}
        prompt = self._build_prompt(template_id, answers)
        validation = self.validator.validate(prompt)
        return {"prompt": prompt, "validation": validation, "files_expected": template["files_generated"]}

    def _build_prompt(self, template_id: str, answers: Dict[str, Any]) -> str:
        template = TEMPLATES[template_id]
        lines = [f"Creá un proyecto de tipo {template['name']} llamado {answers.get('project_name', 'Proyecto')}."]
        for q in template["questions"]:
            qid = q["id"]
            if qid in answers and answers[qid] not in [None, "", False]:
                val = answers[qid]
                if isinstance(val, bool) and val:
                    lines.append(f"- Incluir: {q['question'].replace('¿', '').replace('?', '').strip()}")
                elif isinstance(val, str) and val:
                    lines.append(f"- {q['question'].replace('¿', '').replace('?', '').strip()}: {val}")
        lines.append("Incluí todos los archivos necesarios (backend, frontend, configuración).")
        lines.append("Generá requirements.txt, package.json, Dockerfile y .env.example.")
        lines.append("Usá variables de entorno para secretos.")
        lines.append("El código debe ser funcional y listo para ejecutar.")
        return "\n".join(lines)