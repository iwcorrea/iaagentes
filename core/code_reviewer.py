import re
from pathlib import Path

class CodeReviewer:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)

    def review_backend(self) -> list:
        issues = []
        backend_path = self.workspace_path / "backend"
        if not backend_path.exists():
            return issues

        main_file = backend_path / "main.py"
        schemas_file = backend_path / "schemas.py"
        models_file = backend_path / "models.py"

        # 1. Verificar que todos los routers están en main.py
        if main_file.exists():
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

        # 2. Verificar que cada modelo tenga sus schemas
        if models_file.exists() and schemas_file.exists():
            models_content = models_file.read_text(encoding='utf-8')
            schemas_content = schemas_file.read_text(encoding='utf-8')
            model_classes = re.findall(r"class (\w+)\(.*Base\):", models_content)
            for model in model_classes:
                if model not in schemas_content:
                    issues.append(f"Falta schema para el modelo {model} en schemas.py")

        # 3. Verificar imports relativos
        for py_file in backend_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                content = py_file.read_text(encoding='utf-8')
                # Buscar from .X import Y
                imports = re.findall(r"from\s+(\.\w+)\s+import\s+(\w+)", content)
                for rel_path, name in imports:
                    # Resolver ruta relativa
                    current_dir = py_file.parent
                    target = current_dir / f"{rel_path.lstrip('.')}.py"
                    if not target.exists():
                        issues.append(f"{py_file.name}: importa '{name}' de '{rel_path}' que no existe")
            except:
                pass

        return issues