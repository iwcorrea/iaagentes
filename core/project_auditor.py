import re
import sys
from pathlib import Path

class ProjectAuditor:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)

    def audit(self) -> list:
        issues = []
        issues.extend(self._check_backend_integration())
        issues.extend(self._check_schemas())
        issues.extend(self._check_orphan_files())
        issues.extend(self._check_frontend_structure())
        return issues

    def _check_backend_integration(self) -> list:
        issues = []
        backend_path = self.workspace_path / "backend"
        if not backend_path.exists():
            return issues
        main_file = backend_path / "main.py"
        if not main_file.exists():
            return issues
        main_content = main_file.read_text(encoding='utf-8')
        imported = set(re.findall(r"app\.include_router\((\w+)\.router\)", main_content))
        existing = set()
        for py_file in backend_path.rglob("*.py"):
            if py_file.name in ("__init__.py", "main.py", "schemas.py", "models.py", "database.py"):
                continue
            try:
                if "APIRouter" in py_file.read_text(encoding='utf-8'):
                    existing.add(py_file.stem)
            except:
                pass
        missing = existing - imported
        if missing:
            issues.append(f"Routers no integrados en main.py: {', '.join(missing)}")
        return issues

    def _check_schemas(self) -> list:
        issues = []
        backend_path = self.workspace_path / "backend"
        if not backend_path.exists():
            return issues
        schemas_file = backend_path / "schemas.py"
        if not schemas_file.exists():
            return issues
        schemas_content = schemas_file.read_text(encoding='utf-8')
        for py_file in backend_path.rglob("*.py"):
            if py_file.name in ("__init__.py", "schemas.py"):
                continue
            try:
                content = py_file.read_text(encoding='utf-8')
                matches = re.findall(r"from\s+\.+schemas\s+import\s+(.+)", content)
                for match in matches:
                    names = [n.strip() for n in match.replace("(", "").replace(")", "").split(",")]
                    for name in names:
                        if name and name not in schemas_content:
                            issues.append(f"{py_file.name} importa '{name}' pero no existe en schemas.py")
            except:
                pass
        return issues

    def _check_orphan_files(self) -> list:
        issues = []
        allowed = {"backend", "frontend", "project.json", "project_context.json", "chat.json"}
        for item in self.workspace_path.iterdir():
            if item.name not in allowed:
                issues.append(f"Archivo huérfano en raíz: {item.name}")
        return issues

    def _check_frontend_structure(self) -> list:
        issues = []
        frontend_path = self.workspace_path / "frontend"
        if not frontend_path.exists():
            return issues
        required = {
            "package.json": "Dependencias",
            "vite.config.js": "Configuración de Vite",
            "tailwind.config.js": "Configuración de Tailwind",
            "postcss.config.js": "Configuración de PostCSS",
            "src/main.jsx": "Punto de entrada React",
            "src/App.jsx": "Componente principal",
            "src/index.css": "Estilos Tailwind",
        }
        for file, desc in required.items():
            if not (frontend_path / file).exists():
                issues.append(f"Falta archivo del frontend: {file} ({desc})")
        return issues