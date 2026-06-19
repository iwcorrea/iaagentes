import sys
import traceback
import json
import re
import shutil
import ctypes
import importlib
import time
from pathlib import Path
from datetime import datetime
import concurrent.futures

if sys.platform == 'win32':
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002
    def prevent_sleep():
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
    def allow_sleep():
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
else:
    def prevent_sleep(): pass
    def allow_sleep(): pass

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
from core.project_auditor import ProjectAuditor
from core.prompt_integrity import PromptIntegrity
from core.code_reviewer import CodeReviewer
from core.agent_status import set_all_status, set_agent_status, set_progress

CREWAI_AVAILABLE = True
AGENT_TIMEOUT = 90
MAX_RATE_LIMIT_RETRIES = 3  # Intentos antes de abortar una fase

class TimeoutError(Exception): pass

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
        self.agent_registry.register(CodeAgent(memory=self.memory))
        self.crew_available = CREWAI_AVAILABLE
        self.improvement_queue = ImprovementQueue()
        self.generated_files = []  # Archivos guardados en esta sesión
        self.rate_limit_hits = 0   # Contador de rate‑limits consecutivos

    def _get_agents(self):
        importlib.reload(sys.modules.get("agents.director_agent", None) or importlib.import_module("agents.director_agent"))
        importlib.reload(sys.modules.get("agents.backend_agent", None) or importlib.import_module("agents.backend_agent"))
        importlib.reload(sys.modules.get("agents.frontend_agent", None) or importlib.import_module("agents.frontend_agent"))
        importlib.reload(sys.modules.get("agents.qa_agent", None) or importlib.import_module("agents.qa_agent"))
        importlib.reload(sys.modules.get("agents.repair_agent", None) or importlib.import_module("agents.repair_agent"))
        importlib.reload(sys.modules.get("agents.dependency_agent", None) or importlib.import_module("agents.dependency_agent"))
        
        from agents.director_agent import director_agent
        from agents.backend_agent import backend_agent
        from agents.frontend_agent import frontend_agent
        from agents.qa_agent import qa_agent
        from agents.repair_agent import repair_agent
        from agents.dependency_agent import dependency_agent
        
        return director_agent, backend_agent, frontend_agent, qa_agent, repair_agent, dependency_agent

    def orchestrate_project(self, user_prompt: str, is_modification: bool = False, scope: str = "all", mode: str = "full", turbo: bool = False) -> str:
        prevent_sleep()
        self.generated_files = []
        self.rate_limit_hits = 0
        try:
            director_agent, backend_agent, frontend_agent, qa_agent, repair_agent, dependency_agent = self._get_agents()

            validator = PromptIntegrity()
            validation = validator.validate(user_prompt)
            if not validation["valid"]:
                print("[ARCHITECT] ⚠️ Prompt ambiguo o incompleto. Aplicando mejoras automáticas...")
                user_prompt = validator.build_improved_prompt(user_prompt)
            set_progress(5)

            crew_code = qa_report = ""
            final_project_id = Path(self.workspace_path).name
            set_all_status("idle")
            if is_modification:
                self._backup_project()
            project_context = ""
            if is_modification:
                project_context = self._load_project_context_scoped(scope, mode)

            if self.crew_available:
                set_agent_status("Director IA", "working", "Planificando arquitectura...")
                set_progress(10)
                set_all_status("working")
                try:
                    crew_code, qa_report = self._run_with_rate_limit_retry(
                        self._run_ecommerce_workflow,
                        user_prompt, project_context, is_modification,
                        director_agent, backend_agent, frontend_agent, qa_agent
                    )
                    if not crew_code or crew_code.isspace():
                        raise ValueError("El flujo CrewAI no generó código.")
                    self._save_incremental(crew_code)
                    set_agent_status("Director IA", "done", "Plan completado")
                    set_agent_status("Code Generator", "done", "Backend generado")
                    set_agent_status("Frontend Designer", "done", "Frontend generado")
                    set_all_status("done")
                    set_progress(30)
                except TimeoutError:
                    set_all_status("error", "Timeout en generación")
                    crew_code = self._generate_demo_plan(user_prompt)
                    qa_report = "Timeout en generación."
                except Exception as e:
                    if self._is_rate_limited(str(e)):
                        return self._build_rate_limit_report(final_project_id)
                    set_all_status("error", "Error en generación")
                    crew_code = self._generate_demo_plan(user_prompt)
                    qa_report = "Error en generación."
            else:
                set_all_status("error")
                crew_code = self._generate_demo_plan(user_prompt)
                qa_report = "CrewAI desactivado."

            project_json = Path(self.workspace_path) / "project.json"
            if not project_json.exists():
                project_json.write_text(json.dumps({"name": final_project_id, "created": datetime.now().isoformat()}, indent=2), encoding='utf-8')
            set_all_status("done", "Archivos escritos")
            set_progress(60)

            # Auditoría (solo si no estamos en rate‑limit)
            if self.rate_limit_hits == 0:
                self._run_post_generation_audit(repair_agent)

            # Code Reviewer
            if self.rate_limit_hits == 0:
                self._run_code_reviewer(repair_agent)

            set_progress(75)
            self._save_project_context()

            # Dependencias
            if self.rate_limit_hits == 0:
                set_agent_status("Dependency Manager", "working", "Gestionando dependencias...")
                try:
                    self._ensure_dependencies()
                    set_agent_status("Dependency Manager", "done", "Dependencias completadas")
                except:
                    set_agent_status("Dependency Manager", "error")
            set_progress(85)

            # Limpieza
            print("[ARCHITECT] Aplicando herramientas de limpieza...")
            self._clean_generated_code()
            set_progress(95)

            # Reparación iterativa con límite
            if not turbo and qa_report and "No se ejecutó QA" not in qa_report and self.crew_available and self.rate_limit_hits < MAX_RATE_LIMIT_RETRIES:
                self._run_iterative_repair(repair_agent, crew_code, qa_report)

            # Ejecución final
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
            report = f"🧠 PROYECTO {final_project_id}\nESTADO: {status}\nSALIDA: {execution_result.get('stdout', '')[:200]}\nERROR: {execution_result.get('stderr', '')[:200]}\nQA: {qa_report[:300] if not turbo else 'Turbo: QA omitido'}"
            if self.generated_files:
                report += f"\n📁 Archivos generados: {len(self.generated_files)}"
            set_all_status("done", "Proyecto completado")
            set_progress(100)
            return report
        finally:
            allow_sleep()

    def _run_with_rate_limit_retry(self, func, *args, **kwargs):
        """Reintenta una función si falla por rate‑limit, hasta MAX_RATE_LIMIT_RETRIES."""
        for attempt in range(MAX_RATE_LIMIT_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if self._is_rate_limited(str(e)):
                    self.rate_limit_hits += 1
                    if attempt < MAX_RATE_LIMIT_RETRIES - 1:
                        wait = 2 ** attempt * 5  # Backoff exponencial
                        print(f"[ARCHITECT] Rate‑limit detectado. Reintentando en {wait}s...")
                        time.sleep(wait)
                    else:
                        raise
                else:
                    raise

    def _save_incremental(self, crew_code: str):
        """Guarda cada archivo en el momento en que se genera."""
        execute_plan(crew_code, workspace_base=Path(self.workspace_path))
        for f in Path(self.workspace_path).rglob("*"):
            if f.is_file():
                rel = str(f.relative_to(self.workspace_path))
                if rel not in self.generated_files:
                    self.generated_files.append(rel)

    def _run_post_generation_audit(self, repair_agent):
        prj_auditor = ProjectAuditor(self.workspace_path)
        issues = prj_auditor.audit()
        if issues:
            print(f"[ARCHITECT] Auditor encontró {len(issues)} problemas:")
            for issue in issues:
                print(f"  - {issue}")
            try:
                repaired = repair_agent.kickoff(
                    f"Corrige los siguientes problemas en el proyecto:\n" + "\n".join(f"- {i}" for i in issues) + "\n\nDevuelve archivos corregidos en formato ruta:::código."
                )
                if repaired:
                    code = repaired.raw if hasattr(repaired, 'raw') else str(repaired)
                    if ":::" in code:
                        self._save_incremental(code)
                        print("[ARCHITECT] Problemas reparados automáticamente.")
            except Exception as e:
                if self._is_rate_limited(str(e)):
                    self.rate_limit_hits += 1
                print(f"[ARCHITECT] Error al reparar: {e}")

    def _run_code_reviewer(self, repair_agent):
        print("[ARCHITECT] Ejecutando CodeReviewer...")
        reviewer = CodeReviewer(self.workspace_path)
        review_issues = reviewer.review_backend()
        if review_issues:
            print(f"[ARCHITECT] CodeReviewer encontró {len(review_issues)} problemas:")
            for issue in review_issues:
                print(f"  - {issue}")
            try:
                repaired = repair_agent.kickoff(
                    f"Corrige los siguientes problemas de código:\n" + "\n".join(f"- {i}" for i in review_issues) + "\n\nDevuelve archivos corregidos en formato ruta:::código."
                )
                if repaired:
                    code = repaired.raw if hasattr(repaired, 'raw') else str(repaired)
                    if ":::" in code:
                        self._save_incremental(code)
                        print("[ARCHITECT] Problemas de código reparados automáticamente.")
            except Exception as e:
                if self._is_rate_limited(str(e)):
                    self.rate_limit_hits += 1
                print(f"[ARCHITECT] Error al reparar: {e}")

    def _run_iterative_repair(self, repair_agent, crew_code, qa_report):
        for iteration in range(3):
            if self.rate_limit_hits >= MAX_RATE_LIMIT_RETRIES:
                break
            set_agent_status("Repair Agent", "working", f"Reparación {iteration+1}/3...")
            try:
                reduced_context = self._build_reduced_context(crew_code)
                repair_prompt = f"""CORRIGE el código según el informe de auditoría. Formato ruta:::código.
                INFORME: {qa_report[:500]}
                CÓDIGO (resumen): {reduced_context}
                """
                repaired_code = run_with_timeout(repair_agent.kickoff, AGENT_TIMEOUT, repair_prompt)
                if repaired_code and not str(repaired_code).isspace():
                    repaired_text = repaired_code.raw if hasattr(repaired_code, 'raw') else str(repaired_code)
                    if repaired_text:
                        self._save_incremental(repaired_text)
                        crew_code = repaired_text
                        set_agent_status("Repair Agent", "done", "Reparación aplicada")
            except TimeoutError:
                set_agent_status("Repair Agent", "error", "Timeout en reparación")
            except Exception as e:
                if self._is_rate_limited(str(e)):
                    self.rate_limit_hits += 1
                    print("[ARCHITECT] ⚠️ Límite diario alcanzado. Deteniendo reparaciones.")
                    set_agent_status("Repair Agent", "error", "Límite diario alcanzado")
                    break
                else:
                    set_agent_status("Repair Agent", "error", str(e)[:50])
            if "error" not in qa_report.lower() and "vulnerabilidad" not in qa_report.lower():
                break

    def _run_ecommerce_workflow(self, user_prompt, project_context, is_modification, director_agent, backend_agent, frontend_agent, qa_agent):
        from workflows.ecommerce_workflow import run_ecommerce_workflow
        return run_ecommerce_workflow(user_prompt, project_context, is_modification)

    def _is_rate_limited(self, error_message: str) -> bool:
        return "free-models-per-day" in error_message or "Rate limit exceeded" in error_message or "429" in error_message

    def _build_rate_limit_report(self, project_id: str) -> str:
        return f"🧠 PROYECTO {project_id}\n⏳ LÍMITE DIARIO ALCANZADO\nLos modelos gratuitos de OpenRouter se agotaron por hoy.\nGuardá este ID y continuá mañana cuando se reinicie el límite.\nArchivos ya guardados: {len(self.generated_files)}"

    def _build_reduced_context(self, crew_code: str) -> str:
        lines = crew_code.split('\n')
        reduced = []
        for line in lines:
            if ':::' in line:
                parts = line.split(':::', 1)
                reduced.append(f"{parts[0]}:::")
                code_lines = parts[1].split('\n')[:3]
                reduced.append('\n'.join(code_lines))
                reduced.append('...')
            else:
                reduced.append(line[:200])
        return '\n'.join(reduced[:50])

    def _clean_generated_code(self):
        backend_path = Path(self.workspace_path) / "backend"
        if not backend_path.exists():
            return
        from tools.code_cleaner import clean_backend_code
        result = clean_backend_code(str(backend_path))
        print(f"[ARCHITECT] Limpieza de código completada:\n{result}")

    def _validate_prompt_integrity(self, user_prompt: str) -> dict:
        validator = PromptIntegrity()
        return validator.validate(user_prompt)

    def _build_improved_prompt(self, user_prompt: str) -> str:
        validator = PromptIntegrity()
        return validator.build_improved_prompt(user_prompt)

    def _generate_demo_plan(self, prompt):
        return 'backend/main.py:::from fastapi import FastAPI\napp = FastAPI()\n\n@app.get("/")\ndef root():\n    return {"message": "Hello World"}\n'

    def _backup_project(self):
        src = Path(self.workspace_path)
        if not src.exists(): return
        dst = src.parent / f"{src.name}_backup"
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(src, dst)

    def _load_project_context_scoped(self, scope: str, mode: str) -> str:
        project_path = Path(self.workspace_path)
        if not project_path.exists():
            return ""
        lines = []
        for f in project_path.rglob("*"):
            if f.is_file() and f.name not in ["project_context.json", "chat.json", "project.json"]:
                rel = str(f.relative_to(project_path))
                if scope == "backend" and not rel.startswith("backend"): continue
                if scope == "frontend" and not rel.startswith("frontend"): continue
                if mode == "light":
                    lines.append(f"- {rel}")
                else:
                    try:
                        content = f.read_text(encoding='utf-8')[:1000]
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
        pass