import re
import json
from pathlib import Path
from core.agent_status import set_agent_status, set_progress
from core.dependency_cache import DependencyCache
from core.executor import execute_plan

class PhaseDependencies:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def run(self):
        set_agent_status("Dependency Manager", "working", "Cacheando dependencias...")
        backend_path = Path(self.orchestrator.workspace_path) / "backend"
        frontend_path = Path(self.orchestrator.workspace_path) / "frontend"

        if backend_path.exists():
            self._fix(backend_path, "backend")
        if frontend_path.exists():
            self._fix(frontend_path, "frontend")

        set_agent_status("Dependency Manager", "done", "Dependencias completadas")
        set_progress(85)

    def _fix(self, base_path, project_type):
        cache = DependencyCache()
        imports = self._extract_imports(base_path)
        cached = {i: cache.get(i) for i in imports if cache.get(i)}
        uncached = [i for i in imports if not cache.get(i)]

        if not uncached and cached:
            deps = sorted(set(cached.values()))
            base = {"fastapi", "uvicorn", "sqlalchemy", "python-jose", "passlib", "python-multipart", "python-dotenv"}
            all_deps = sorted(base | set(deps))
            execute_plan(f"backend/requirements.txt:::{chr(10).join(all_deps)}",
                         workspace_base=Path(self.orchestrator.workspace_path))
            return

        if uncached:
            from agents.dependency_agent import dependency_agent
            prompt = f"Paquete pip para:\n" + "\n".join(f"- {i}" for i in uncached) + "\n\nJSON:"
            try:
                response = dependency_agent.kickoff(prompt)
                if response:
                    text = response.raw if hasattr(response, 'raw') else str(response)
                    new_map = json.loads(text)
                    for imp, pkg in new_map.items():
                        cache.add(imp, pkg)
                        cached[imp] = pkg
            except Exception:
                pass

        if cached:
            deps = sorted(set(cached.values()))
            base = {"fastapi", "uvicorn", "sqlalchemy", "python-jose", "passlib", "python-multipart", "python-dotenv"}
            all_deps = sorted(base | set(deps))
            execute_plan(f"backend/requirements.txt:::{chr(10).join(all_deps)}",
                         workspace_base=Path(self.orchestrator.workspace_path))

    def _extract_imports(self, base_path):
        imports = set()
        for f in base_path.rglob("*.py"):
            try:
                content = f.read_text(encoding='utf-8')
                imports.update(re.findall(r'^(?:from|import)\s+(\w+)', content, re.MULTILINE))
            except:
                pass
        return imports