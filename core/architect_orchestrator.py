import sys
import traceback
import json
import re
import shutil
from pathlib import Path
from datetime import datetime
import concurrent.futures

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
AGENT_TIMEOUT = 90  # segundos


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
        crew_code = ""
        qa_report = ""
        final_project_id = Path(self.workspace_path).name

        set_all_status("idle")

        # Backup automático si es modificación
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
                    AGENT_TIMEOUT * 2,  # más tiempo para el workflow completo
                    user_prompt,
                    project_context,
                    is_modification
                )
                if not crew_code or crew_code.isspace():
                    raise ValueError("El flujo CrewAI no generó código.")
                set_all_status("done")
                print("[ARCHITECT] Generación de código completada.")
            except TimeoutError:
                set_all_status("error")
                print(f"[ARCHITECT] Timeout en generación CrewAI. Usando plan DEMO.")
                crew_code = self._generate_demo_plan(user_prompt)
                qa_report = "Timeout en generación."
            except Exception as e:
                set_all_status("error")
                print(f"[ARCHITECT] Falló generación CrewAI: {e}. Usando plan DEMO.")
                crew_code = self._generate_demo_plan(user_prompt)
                qa_report = "No se ejecutó QA (plan DEMO)."
        else:
            set_all_status("error")
            print("[ARCHITECT] Fase 1: Usando modo DEMO (CrewAI desactivado).")
            crew_code = self._generate_demo_plan(user_prompt)
            qa_report = "CrewAI desactivado."

        # ─── FASE 2: ESCRITURA DE ARCHIVOS ───
        execution_summary = execute_plan(crew_code, workspace_base=Path(self.workspace_path))

        project_json_path = Path(self.workspace_path) / "project.json"
        if not project_json_path.exists():
            project_json_path.write_text(json.dumps({
                "name": final_project_id,
                "created": datetime.now().isoformat()
            }, indent=2), encoding='utf-8')

        # ─── FASE 2.1: VALIDACIÓN DE INTEGRIDAD ───
        self._validate_integration_extended()

        self._save_project_context()

        # ─── FASE 2.5: DEPENDENCIAS ───
        print("[ARCHITECT] Verificando dependencias...")
        set_agent_status("Dependency Manager", "working")
        try:
            self._ensure_dependencies()
            set_agent_status("Dependency Manager", "done")
        except Exception as e:
            set_agent_status("Dependency Manager", "error")
            print(f"[ARCHITECT] Error en dependencias: {e}")

        # ─── FASE 3: REPARACIÓN (solo si no es modo turbo) ───
        if not turbo and qa_report and "No se ejecutó QA" not in qa_report and self.crew_available:
            for iteration in range(3):
                print(f"[ARCHITECT] Reparación iterativa {iteration+1}...")
                set_agent_status("Repair Agent", "working")
                try:
                    repair_prompt = f"""
CORRIGE el siguiente código según el informe de auditoría.
Devuelve el código corregido en formato ruta:::código.

INFORME:
{qa_report}

CÓDIGO:
{crew_code}
"""
                    repaired_code = run_with_timeout(repair_agent.kickoff, AGENT_TIMEOUT, repair_prompt)

                    if repaired_code and not str(repaired_code).isspace():
                        repaired_text = repaired_code.raw if hasattr(repaired_code, 'raw') else str(repaired_code)
                        if repaired_text and not repaired_text.isspace():
                            execute_plan(repaired_text, workspace_base=Path(self.workspace_path))
                            crew_code = repaired_text
                            set_agent_status("Repair Agent", "done")
                            self._validate_integration_extended()
                except TimeoutError:
                    set_agent_status("Repair Agent", "error")
                    print("[ARCHITECT] Timeout en reparación.")
                except Exception as e:
                    set_agent_status("Repair Agent", "error")
                    print(f"[ARCHITECT] Error en reparación: {e}")

                if "error" not in qa_report.lower() and "vulnerabilidad" not in qa_report.lower():
                    print("[ARCHITECT] QA limpio. Fin de reparaciones.")
                    break

        # ─── FASE 4: ANÁLISIS Y EJECUCIÓN ───
        try:
            print("[ARCHITECT] Escaneando estructura...")
            self.memory.scan_project()
            initial_issues = self.memory.validate()
            if initial_issues:
                self.memory.fix_imports_globally()

            print("[ARCHITECT] Ejecutando refactorización...")
            refactor_log = self.refactor.analyze_and_fix(extended=True)
            if refactor_log:
                self.memory.scan_project()

            print("[ARCHITECT] Ejecutando proyecto...")
            executor = ProjectExecutor(str(self.workspace_path), memory=self.memory)
            execution_result = executor.execute_project()

            meta_proposals = 0
            try:
                print("[ARCHITECT] MetaAgent analizando...")
                meta = MetaAgent(memory=self.memory, queue=self.improvement_queue)
                proposal_ids = meta.analyze_and_propose(project_root=".")
                meta_proposals = len(proposal_ids)
                if meta_proposals > 0:
                    print(f"[ARCHITECT] MetaAgent generó {meta_proposals} propuestas.")
            except Exception as e:
                print(f"[ARCHITECT] MetaAgent error: {e}")

            try:
                context_summary = self.context.summary()
            except:
                context_summary = {"models": "N/A", "routes": "N/A", "entities": "N/A"}

            final_issues = self.memory.validate()
            success = execution_result.get('success', False)
            status = "✅ SALUDABLE" if success and not final_issues else "⚠️ REQUIERE ATENCIÓN"

            report = f"""
🧠 PROYECTO {final_project_id}
ESTADO: {status}
TIPO: {execution_result.get('execution_type', 'desconocido')}
SALIDA: {execution_result.get('stdout', '')[:200]}
ERROR: {execution_result.get('stderr', '')[:200]}
QA: {qa_report[:300] if not turbo else 'Modo turbo: QA omitido'}
"""
            return report

        except Exception as e:
            return f"ERROR:\n{traceback.format_exc()}"

    # ─── VALIDACIÓN DE INTEGRIDAD EXTENDIDA ───
    def _validate_integration_extended(self):
        backend_path = Path(self.workspace_path) / "backend"
        if not backend_path.exists():
            return

        main_file = backend_path / "main.py"
        if not main_file.exists():
            print("[ARCHITECT] ⚠️ No se encontró main.py.")
            return

        main_content = main_file.read_text(encoding='utf-8')
        schemas_file = backend_path / "schemas.py"
        schemas_content = schemas_file.read_text(encoding='utf-8') if schemas_file.exists() else ""

        issues = []

        # Routers no integrados
        import_pattern = r"app\.include_router\((\w+)\.router\)"
        imported_routers = set(re.findall(import_pattern, main_content))
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

        # Schemas no definidos
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
                            issues.append(f"{py_file.name} importa '{name}' de schemas pero no existe")
            except:
                pass

        if issues:
            print(f"[ARCHITECT] ⚠️ Problemas de integridad: {len(issues)}")
            repair_prompt = f"""
Corrige los siguientes problemas:
{chr(10).join(f'- {i}' for i in issues)}

Devuelve archivos corregidos en formato ruta:::código.
"""
            try:
                repaired = repair_agent.kickoff(repair_prompt)
                if repaired:
                    code = repaired.raw if hasattr(repaired, 'raw') else str(repaired)
                    if ":::" in code:
                        execute_plan(code, workspace_base=Path(self.workspace_path))
                        print("[ARCHITECT] ✅ Integridad reparada.")
            except Exception as e:
                print(f"[ARCHITECT] Error al reparar integridad: {e}")

    # ─── BACKUP ───
    def _backup_project(self):
        src = Path(self.workspace_path)
        if not src.exists():
            return
        dst = src.parent / f"{src.name}_backup"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"[ARCHITECT] Backup creado en {dst}")

    # ─── CONTEXTO COMPRIMIDO ───
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
                        lines.append(f"=== {rel} ===\n[binario]")
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
        prompt = f"""
Genera archivo de dependencias para {project_type} con archivos: {', '.join(code_files[:10])}.
Formato: path:::code.
"""
        try:
            response = dependency_agent.kickoff(prompt)
            if response:
                dep_code = response.raw if hasattr(response, 'raw') else str(response)
                if dep_code:
                    execute_plan(dep_code, workspace_base=Path(self.workspace_path))
        except Exception as e:
            print(f"[ARCHITECT] Error dependencias: {e}")

    def _generate_demo_plan(self, prompt):
        return (
            'backend/main.py:::from fastapi import FastAPI\n'
            'app = FastAPI()\n\n'
            '@app.get("/")\n'
            'def root():\n'
            '    return {"message": "Hello World"}\n'
        )