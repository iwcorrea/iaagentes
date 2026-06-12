import sys
import traceback
import json
import re
import shutil
import ctypes
from pathlib import Path
from datetime import datetime
import concurrent.futures

# ─── BLOQUEO DE SUSPENSIÓN (Windows) ───
if sys.platform == 'win32':
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002

    def prevent_sleep():
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )

    def allow_sleep():
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
else:
    def prevent_sleep():
        pass
    def allow_sleep():
        pass

ROOT_DIR = Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.architecture_memory import ArchitectureMemory
from core.global_context import GlobalContext
from core.executor import ProjectExecutor, execute_plan
from core.refactor_engine import RefactorEngine
from core.agents.registry import AgentRegistry
from core.simulated_agents import CodeAgent
from core.improvement_queue import ImprovementQueue
from core.meta_agent import MetaAgent
from core.plan_validator import PlanValidator
from workflows.ecommerce_workflow import run_ecommerce_workflow
from agents.repair_agent import repair_agent
from agents.dependency_agent import dependency_agent
from core.agent_status import set_all_status, set_agent_status

CREWAI_AVAILABLE = True
AGENT_TIMEOUT = 90


class TimeoutError(Exception):
    pass


def run_with_timeout(func, timeout, *args, **kwargs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise TimeoutError(f"Timeout después de {timeout}s")


class AutonomousArchitectOrchestrator:
    def __init__(self, workspace_path="workspace"):
        self.workspace_path = workspace_path
        self.memory = ArchitectureMemory(root_path=str(Path(workspace_path) / "backend"))
        self.context = GlobalContext()
        self.refactor = RefactorEngine(self.memory)
        self.plan_validator = PlanValidator()

        self.agent_registry = AgentRegistry()
        code_agent = CodeAgent(memory=self.memory)
        self.agent_registry.register(code_agent)

        self.crew_available = CREWAI_AVAILABLE
        self.improvement_queue = ImprovementQueue()

    def orchestrate_project(self, user_prompt: str, is_modification: bool = False, scope: str = "all", mode: str = "full", turbo: bool = False) -> str:
        prevent_sleep()
        try:
            crew_code = ""
            qa_report = ""
            final_project_id = Path(self.workspace_path).name

            set_all_status("idle")

            if is_modification:
                self._backup_project()

            project_context = ""
            if is_modification:
                project_context = self._load_project_context_scoped(scope, mode)

            # ─── FASE 1: GENERACIÓN ───
            if self.crew_available:
                print(f"[ARCHITECT] Fase 1: Iniciando CrewAI (turbo={turbo})...")
                set_all_status("working")
                try:
                    crew_code, qa_report = run_with_timeout(
                        run_ecommerce_workflow,
                        AGENT_TIMEOUT * 2,
                        user_prompt,
                        project_context,
                        is_modification
                    )
                    if not crew_code or crew_code.isspace():
                        raise ValueError("El flujo CrewAI no generó código.")
                    set_all_status("done")
                    print("[ARCHITECT] Generación completada.")
                except TimeoutError:
                    set_all_status("error")
                    crew_code = self._generate_demo_plan(user_prompt)
                    qa_report = "Timeout en generación."
                except Exception as e:
                    set_all_status("error")
                    crew_code = self._generate_demo_plan(user_prompt)
                    qa_report = "Error en generación."
            else:
                set_all_status("error")
                crew_code = self._generate_demo_plan(user_prompt)
                qa_report = "CrewAI desactivado."

            # ─── FASE 2: ESCRITURA ───
            execute_plan(crew_code, workspace_base=Path(self.workspace_path))
            project_json_path = Path(self.workspace_path) / "project.json"
            if not project_json_path.exists():
                project_json_path.write_text(json.dumps({
                    "name": final_project_id,
                    "created": datetime.now().isoformat()
                }, indent=2), encoding='utf-8')

            # ─── VALIDACIONES ───
            self._validate_integration_extended()
            self._validate_frontend_structure()
            self._clean_orphan_files()
            self._save_project_context()

            # ─── DEPENDENCIAS ───
            set_agent_status("Dependency Manager", "working")
            try:
                self._ensure_dependencies()
                set_agent_status("Dependency Manager", "done")
            except:
                set_agent_status("Dependency Manager", "error")

            # ─── REPARACIÓN ───
            if not turbo and qa_report and "No se ejecutó QA" not in qa_report and self.crew_available:
                for iteration in range(3):
                    set_agent_status("Repair Agent", "working")
                    try:
                        repair_prompt = f"""CORRIGE el código según el informe de auditoría. Formato ruta:::código.

INFORME:
{qa_report}

CÓDIGO:
{crew_code}
"""
                        repaired_code = run_with_timeout(repair_agent.kickoff, AGENT_TIMEOUT, repair_prompt)
                        if repaired_code and not str(repaired_code).isspace():
                            repaired_text = repaired_code.raw if hasattr(repaired_code, 'raw') else str(repaired_code)
                            if repaired_text:
                                execute_plan(repaired_text, workspace_base=Path(self.workspace_path))
                                crew_code = repaired_text
                                set_agent_status("Repair Agent", "done")
                                self._validate_integration_extended()
                                self._validate_frontend_structure()
                    except TimeoutError:
                        set_agent_status("Repair Agent", "error")
                    except:
                        set_agent_status("Repair Agent", "error")
                    if "error" not in qa_report.lower() and "vulnerabilidad" not in qa_report.lower():
                        break

            # ─── EJECUCIÓN ───
            self.memory.scan_project()
            self.memory.fix_imports_globally()
            self.refactor.analyze_and_fix(extended=True)
            executor = ProjectExecutor(str(self.workspace_path), memory=self.memory)
            execution_result = executor.execute_project()

            try:
                MetaAgent(memory=self.memory, queue=self.improvement_queue).analyze_and_propose(project_root=".")
            except:
                pass

            success = execution_result.get('success', False)
            status = "✅ SALUDABLE" if success else "⚠️ REQUIERE ATENCIÓN"
            return f"""
🧠 PROYECTO {final_project_id}
ESTADO: {status}
SALIDA: {execution_result.get('stdout', '')[:200]}
ERROR: {execution_result.get('stderr', '')[:200]}
QA: {qa_report[:300] if not turbo else 'Turbo: QA omitido'}
"""
        finally:
            allow_sleep()

    # ─── VALIDACIONES ───
    def _validate_integration_extended(self):
        backend_path = Path(self.workspace_path) / "backend"
        if not backend_path.exists():
            return
        main_file = backend_path / "main.py"
        if not main_file.exists():
            return
        main_content = main_file.read_text(encoding='utf-8')
        schemas_file = backend_path / "schemas.py"
        schemas_content = schemas_file.read_text(encoding='utf-8') if schemas_file.exists() else ""
        issues = []
        imported_routers = set(re.findall(r"app\.include_router\((\w+)\.router\)", main_content))
        existing_routers = set()
        for py_file in backend_path.rglob("*.py"):
            if py_file.name in ["__init__.py", "main.py", "schemas.py", "models.py", "database.py"]:
                continue
            try:
                content = py_file.read_text(encoding='utf-8')
                if "APIRouter" in content:
                    existing_routers.add(py_file.stem)
            except:
                pass
        missing = existing_routers - imported_routers
        if missing:
            issues.append(f"Routers no integrados en main.py: {', '.join(missing)}")
        for py_file in backend_path.rglob("*.py"):
            if py_file.name == "schemas.py" or py_file.name == "__init__.py":
                continue
            try:
                content = py_file.read_text(encoding='utf-8')
                matches = re.findall(r"from\s+\.+schemas\s+import\s+(.+)", content)
                for match in matches:
                    names = [n.strip() for n in match.replace("(", "").replace(")", "").split(",")]
                    for name in names:
                        if name and name not in schemas_content:
                            issues.append(f"{py_file.name} importa '{name}' de schemas pero no existe en schemas.py")
            except:
                pass
        if issues:
            repair_prompt = f"""
Corrige los siguientes problemas de integridad:
{chr(10).join(f'- {i}' for i in issues)}

Devuelve archivos corregidos en formato ruta:::código.
"""
            try:
                repaired = repair_agent.kickoff(repair_prompt)
                if repaired:
                    code = repaired.raw if hasattr(repaired, 'raw') else str(repaired)
                    if ":::" in code:
                        execute_plan(code, workspace_base=Path(self.workspace_path))
            except:
                pass

    def _validate_frontend_structure(self):
        frontend_path = Path(self.workspace_path) / "frontend"
        if not frontend_path.exists():
            return
        required_files = {
            "package.json": "Define dependencias.",
            "vite.config.js": "Configura Vite.",
            "tailwind.config.js": "Configura Tailwind.",
            "postcss.config.js": "Configura PostCSS.",
            "src/main.jsx": "Punto de entrada React.",
            "src/App.jsx": "Componente principal.",
            "src/index.css": "Estilos Tailwind.",
            "src/components/Login.jsx": "Componente de login.",
            "src/components/Dashboard.jsx": "Panel principal."
        }
        missing_files = [(f, d) for f, d in required_files.items() if not (frontend_path / f).exists()]
        if missing_files:
            print(f"[ARCHITECT] ⚠️ Faltan archivos del frontend: {[f[0] for f in missing_files]}")
            repair_prompt = f"""
Faltan los siguientes archivos en el frontend. Generá cada uno usando el formato ruta:::código.
{chr(10).join([f'{f[0]} – {f[1]}' for f in missing_files])}

Reglas:
- package.json debe incluir react, react-dom, react-router-dom, axios, tailwindcss, postcss, autoprefixer, vite, @vitejs/plugin-react.
- Login.jsx y Dashboard.jsx deben ser funcionales y usar axios para la API.
- App.jsx debe tener React Router con rutas protegidas.
- El código debe ser moderno y listo para ejecutar.
"""
            try:
                repaired = repair_agent.kickoff(repair_prompt)
                if repaired:
                    code = repaired.raw if hasattr(repaired, 'raw') else str(repaired)
                    if ":::" in code:
                        execute_plan(code, workspace_base=Path(self.workspace_path))
                        print("[ARCHITECT] ✅ Archivos del frontend generados automáticamente.")
            except Exception as e:
                print(f"[ARCHITECT] Error al generar archivos del frontend: {e}")

    def _clean_orphan_files(self):
        """Elimina archivos/carpetas en la raíz del proyecto que no pertenecen a backend/ ni frontend/."""
        root = Path(self.workspace_path)
        allowed = {"backend", "frontend", "project.json", "project_context.json", "chat.json"}
        for item in root.iterdir():
            if item.name not in allowed:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                print(f"[ARCHITECT] 🧹 Eliminado archivo huérfano: {item.name}")

    def _backup_project(self):
        src = Path(self.workspace_path)
        if not src.exists():
            return
        dst = src.parent / f"{src.name}_backup"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    def _load_project_context_scoped(self, scope: str, mode: str) -> str:
        project_path = Path(self.workspace_path)
        if not project_path.exists():
            return ""
        lines = []
        for f in project_path.rglob("*"):
            if f.is_file() and f.name not in ["project_context.json", "chat.json", "project.json"]:
                rel = str(f.relative_to(project_path))
                if scope == "backend" and not rel.startswith("backend"):
                    continue
                if scope == "frontend" and not rel.startswith("frontend"):
                    continue
                if mode == "light":
                    lines.append(f"- {rel}")
                else:
                    try:
                        content = f.read_text(encoding='utf-8')
                        if len(content) > 500:
                            lines.append(f"=== {rel} ===\n{content[:500]}\n... (truncado)")
                        else:
                            lines.append(f"=== {rel} ===\n{content}")
                    except:
                        pass
        return "\n".join(lines)

    def _save_project_context(self):
        pass

    def _ensure_dependencies(self):
        backend_path = Path(self.workspace_path) / "backend"
        frontend_path = Path(self.workspace_path) / "frontend"
        if backend_path.exists():
            req_file = backend_path / "requirements.txt"
            if not req_file.exists() or len(req_file.read_text(encoding='utf-8').strip()) < 20:
                self._fix_dependencies(backend_path, "backend")
        if frontend_path.exists():
            pkg_file = frontend_path / "package.json"
            if not pkg_file.exists() or len(pkg_file.read_text(encoding='utf-8').strip()) < 20:
                self._fix_dependencies(frontend_path, "frontend")

    def _fix_dependencies(self, base_path: Path, project_type: str):
        code_files = []
        for ext in ['.py', '.jsx', '.js']:
            for f in base_path.rglob(f'*{ext}'):
                if f.name not in ["requirements.txt", "package.json"]:
                    code_files.append(str(f.relative_to(base_path)))
        if not code_files:
            return
        prompt = f"Genera archivo de dependencias para {project_type} con archivos: {', '.join(code_files[:10])}. Formato: path:::code."
        try:
            response = dependency_agent.kickoff(prompt)
            if response:
                dep_code = response.raw if hasattr(response, 'raw') else str(response)
                if dep_code:
                    execute_plan(dep_code, workspace_base=Path(self.workspace_path))
        except:
            pass

    def _generate_demo_plan(self, prompt):
        return (
            'backend/main.py:::from fastapi import FastAPI\n'
            'app = FastAPI()\n\n'
            '@app.get("/")\n'
            'def root():\n'
            '    return {"message": "Hello World"}\n'
        )