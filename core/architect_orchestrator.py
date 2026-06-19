import sys
import traceback
import json
import re
import shutil
import ctypes
import importlib
import time
import os
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
from core.dependency_cache import DependencyCache
from core.agent_status import set_all_status, set_agent_status, set_progress

CREWAI_AVAILABLE = True
AGENT_TIMEOUT = 90
MAX_RATE_LIMIT_RETRIES = 3

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
        self.generated_files = []
        self.rate_limit_hits = 0

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
            set_agent_status("Director IA", "working", "Analizando prompt...")

            crew_code = qa_report = ""
            final_project_id = Path(self.workspace_path).name
            set_all_status("idle")
            if is_modification:
                self._backup_project()
            project_context = ""
            if is_modification:
                project_context = self._load_project_context_scoped(scope, mode)

            if self.crew_available:
                set_agent_status("Director IA", "working", "Planificando estructura de archivos...")
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

            if self.rate_limit_hits == 0:
                set_agent_status("QA Auditor", "working", "Revisando código generado...")
                self._run_post_generation_audit(repair_agent)
                set_agent_status("QA Auditor", "done", "Auditoría completada")

            if self.rate_limit_hits == 0:
                set_agent_status("QA Auditor", "working", "Analizando estructura de código...")
                self._run_code_reviewer(repair_agent)
                set_agent_status("QA Auditor", "done", "Code review completada")

            set_progress(65)

            # ─── VALIDACIÓN DE SINTAXIS ───
            print("[ARCHITECT] Validando sintaxis de archivos...")
            self._validate_syntax()
            set_progress(70)

            set_progress(75)
            self._save_project_context()

            if self.rate_limit_hits == 0:
                set_agent_status("Dependency Manager", "working", "Cacheando dependencias...")
                try:
                    self._ensure_dependencies()
                    set_agent_status("Dependency Manager", "done", "Dependencias completadas")
                except:
                    set_agent_status("Dependency Manager", "error")
            set_progress(85)

            print("[ARCHITECT] Aplicando herramientas de limpieza...")
            self._clean_generated_code()
            set_progress(88)

            if not turbo and self.crew_available and self.rate_limit_hits < MAX_RATE_LIMIT_RETRIES:
                print("[ARCHITECT] Generando tests unitarios...")
                try:
                    from agents.test_agent import test_agent
                    self._generate_tests(test_agent)
                except Exception as e:
                    print(f"[ARCHITECT] Error al generar tests: {e}")
            set_progress(92)

            # ─── DESPLIEGUE Y DOCUMENTACIÓN ───
            if not turbo and self.crew_available and self.rate_limit_hits < MAX_RATE_LIMIT_RETRIES:
                print("[ARCHITECT] Generando archivos de despliegue y documentación...")
                try:
                    from agents.deploy_agent import deploy_agent
                    self._generate_deploy_and_docs(deploy_agent)
                except Exception as e:
                    print(f"[ARCHITECT] Error al generar despliegue/docs: {e}")
            set_progress(96)

            if not turbo and qa_report and "No se ejecutó QA" not in qa_report and self.crew_available and self.rate_limit_hits < MAX_RATE_LIMIT_RETRIES:
                set_agent_status("Repair Agent", "working", "Aplicando correcciones...")
                self._run_iterative_repair(repair_agent, crew_code, qa_report)
                set_agent_status("Repair Agent", "done", "Reparaciones finalizadas")

            self.memory.scan_project()
            self.memory.fix_imports_globally()
            self.refactor.analyze_and_fix(extended=True)
            executor = ProjectExecutor(str(self.workspace_path), memory=self.memory)
            execution_result = executor.execute_project()
            try:
                MetaAgent(memory=self.memory, queue=self.improvement_queue).analyze_and_propose(project_root=".")
            except:
                pass

            # ─── REGISTRAR APRENDIZAJE ───
            self._track_learning(final_project_id)

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
        for attempt in range(MAX_RATE_LIMIT_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if self._is_rate_limited(str(e)):
                    self.rate_limit_hits += 1
                    if attempt < MAX_RATE_LIMIT_RETRIES - 1:
                        wait = 2 ** attempt * 5
                        print(f"[ARCHITECT] Rate‑limit detectado. Reintentando en {wait}s...")
                        time.sleep(wait)
                    else:
                        raise
                else:
                    raise

    def _save_incremental(self, crew_code: str):
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
            except TimeoutError:
                pass
            except Exception as e:
                if self._is_rate_limited(str(e)):
                    self.rate_limit_hits += 1
                    print("[ARCHITECT] ⚠️ Límite diario alcanzado. Deteniendo reparaciones.")
                    break
            if "error" not in qa_report.lower() and "vulnerabilidad" not in qa_report.lower():
                break

    def _run_ecommerce_workflow(self, user_prompt, project_context, is_modification, director_agent, backend_agent, frontend_agent, qa_agent):
        from workflows.ecommerce_workflow import run_ecommerce_workflow
        return run_ecommerce_workflow(user_prompt, project_context, is_modification)

    def _is_rate_limited(self, error_message: str) -> bool:
        return "free-models-per-day" in error_message or "Rate limit exceeded" in error_message or "429" in error_message

    def _build_rate_limit_report(self, project_id: str) -> str:
        return f"🧠 PROYECTO {project_id}\n⏳ LÍMITE DIARIO ALCANZADO\nLos modelos gratuitos de OpenRouter se agotaron por hoy.\nGuardá este ID y continuá cuando se reinicie el límite.\nArchivos ya guardados: {len(self.generated_files)}"

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

    def _generate_tests(self, test_agent):
        backend_path = Path(self.workspace_path) / "backend"
        if not backend_path.exists():
            return
        code_files = []
        for py_file in backend_path.rglob("*.py"):
            if py_file.name != "__init__.py":
                try:
                    content = py_file.read_text(encoding='utf-8')
                    code_files.append(f"=== {py_file.name} ===\n{content[:1500]}")
                except:
                    pass
        if not code_files:
            return
        prompt = f"""Generá tests unitarios con pytest para el siguiente backend.
Usá TestClient de FastAPI y pytest.
Formato: ruta:::código.

CÓDIGO DEL BACKEND:
{chr(10).join(code_files[:5])}
"""
        try:
            response = test_agent.kickoff(prompt)
            if response:
                test_code = response.raw if hasattr(response, 'raw') else str(response)
                if test_code and ":::" in test_code:
                    execute_plan(test_code, workspace_base=Path(self.workspace_path))
                    print("[ARCHITECT] Tests generados automáticamente.")
        except Exception as e:
            print(f"[ARCHITECT] Error generando tests: {e}")

    def _validate_syntax(self):
        """Ejecuta el validador de sintaxis y repara errores automáticamente."""
        from core.syntax_validator import SyntaxValidator
        validator = SyntaxValidator(self.workspace_path)
        syntax_errors = validator.validate_all()
        if syntax_errors:
            print(f"[ARCHITECT] SyntaxValidator encontró {len(syntax_errors)} errores:")
            for error in syntax_errors:
                print(f"  - {error}")
            if self.rate_limit_hits < MAX_RATE_LIMIT_RETRIES:
                repair_prompt = f"""Corregí los siguientes errores de sintaxis en los archivos del proyecto.
Devolvé los archivos corregidos en formato ruta:::código.

ERRORES:
{chr(10).join(f'- {e}' for e in syntax_errors)}
"""
                try:
                    from agents.repair_agent import repair_agent
                    repaired = repair_agent.kickoff(repair_prompt)
                    if repaired:
                        code = repaired.raw if hasattr(repaired, 'raw') else str(repaired)
                        if ":::" in code:
                            self._save_incremental(code)
                            print("[ARCHITECT] Errores de sintaxis reparados automáticamente.")
                except Exception as e:
                    print(f"[ARCHITECT] Error al reparar sintaxis: {e}")
        else:
            print("[ARCHITECT] ✅ Sintaxis válida en todos los archivos.")

    def _generate_deploy_and_docs(self, deploy_agent):
        """Genera archivos de despliegue y documentación."""
        backend_path = Path(self.workspace_path) / "backend"

        project_info = []
        if backend_path.exists():
            for py_file in backend_path.rglob("*.py"):
                if py_file.name != "__init__.py":
                    try:
                        content = py_file.read_text(encoding='utf-8')
                        project_info.append(f"=== {py_file.relative_to(self.workspace_path)} ===\n{content[:1000]}")
                    except:
                        pass

        prompt = f"""Generá los archivos de despliegue y documentación para este proyecto.
Usá el formato ruta:::código.

INFORMACIÓN DEL PROYECTO:
{chr(10).join(project_info[:5])}

Generá:
1. Dockerfile
2. docker-compose.yml
3. .env.example
4. README.md
"""
        try:
            response = deploy_agent.kickoff(prompt)
            if response:
                deploy_code = response.raw if hasattr(response, 'raw') else str(response)
                if deploy_code and ":::" in deploy_code:
                    self._save_incremental(deploy_code)
                    print("[ARCHITECT] Archivos de despliegue y documentación generados.")
        except Exception as e:
            print(f"[ARCHITECT] Error generando despliegue/docs: {e}")

    def _track_learning(self, final_project_id: str):
        """Registra el proyecto actual en el rastreador de aprendizaje."""
        from core.learning_tracker import LearningTracker

        tracker = LearningTracker()
        summary = {
            "files": self.generated_files,
            "errors": [],
            "dependencies_cached": True,
            "model_used": os.getenv("CURRENT_BRAIN_MODEL", "unknown"),
            "generated_at": datetime.now().isoformat()
        }

        prj_auditor = ProjectAuditor(self.workspace_path)
        audit_issues = prj_auditor.audit()
        if audit_issues:
            summary["errors"].extend(audit_issues)

        tracker.add_project(final_project_id, summary)
        print(f"[ARCHITECT] Proyecto registrado en el rastreador de aprendizaje.")

        insights = tracker.get_insights()
        if insights.get("total_projects", 0) >= 2:
            print(f"[ARCHITECT] 📊 Estadísticas acumuladas: {insights}")

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
        cache = DependencyCache()

        code_files = []
        for ext in ['.py', '.jsx', '.js']:
            for f in base_path.rglob(f'*{ext}'):
                if f.name not in ["requirements.txt", "package.json"]:
                    code_files.append(str(f.relative_to(base_path)))
        if not code_files:
            return

        known_imports = set()
        for f in code_files:
            full_path = base_path / f
            try:
                content = full_path.read_text(encoding='utf-8')
                if f.endswith('.py'):
                    import_matches = re.findall(r'^(?:from|import)\s+(\w+)', content, re.MULTILINE)
                    known_imports.update(import_matches)
                elif f.endswith(('.js', '.jsx')):
                    import_matches = re.findall(r'import\s+.*?from\s+[\'"]([\w@/.-]+)', content)
                    known_imports.update(import_matches)
            except:
                pass

        cached_deps = {}
        uncached_imports = []
        for imp in sorted(known_imports):
            pkg = cache.get(imp)
            if pkg:
                cached_deps[imp] = pkg
            else:
                uncached_imports.append(imp)

        if not uncached_imports and cached_deps:
            if project_type == "backend":
                deps = sorted(set(cached_deps.values()))
                base_deps = {"fastapi", "uvicorn", "sqlalchemy", "python-jose", "passlib", "python-multipart", "python-dotenv"}
                all_deps = sorted(base_deps | set(deps))
                execute_plan(f"backend/requirements.txt:::{chr(10).join(all_deps)}", workspace_base=Path(self.workspace_path))
                print(f"[ARCHITECT] Dependencias generadas desde caché ({len(all_deps)} paquetes).")
                return

        if uncached_imports:
            from agents.dependency_agent import dependency_agent
            prompt = f"""Identificá el paquete pip necesario para cada uno de estos imports de Python:
{chr(10).join(f'- {imp}' for imp in uncached_imports)}

Respondé en formato JSON: {{"import": "paquete"}}
Solo devolvé el JSON, sin explicaciones.
"""
            try:
                response = dependency_agent.kickoff(prompt)
                if response:
                    text = response.raw if hasattr(response, 'raw') else str(response)
                    try:
                        new_mappings = json.loads(text)
                        for imp, pkg in new_mappings.items():
                            cache.add(imp, pkg)
                            cached_deps[imp] = pkg
                        print(f"[ARCHITECT] Caché actualizada con {len(new_mappings)} nuevas dependencias.")
                    except json.JSONDecodeError:
                        print("[ARCHITECT] No se pudo parsear la respuesta del agente. Usando solo caché.")
            except Exception as e:
                print(f"[ARCHITECT] Error consultando dependencias: {e}")

        if cached_deps:
            base_deps = {"fastapi", "uvicorn", "sqlalchemy", "python-jose", "passlib", "python-multipart", "python-dotenv"}
            all_deps = sorted(base_deps | set(cached_deps.values()))
            execute_plan(f"backend/requirements.txt:::{chr(10).join(all_deps)}", workspace_base=Path(self.workspace_path))
            print(f"[ARCHITECT] Dependencias generadas (caché + LLM): {len(all_deps)} paquetes.")