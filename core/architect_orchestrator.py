import sys
import traceback
import json
import re
from pathlib import Path
from datetime import datetime

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

    def orchestrate_project(self, user_prompt: str, is_modification: bool = False, scope: str = "all", mode: str = "full") -> str:
        crew_code = ""
        qa_report = ""
        final_project_id = Path(self.workspace_path).name

        set_all_status("idle")

        project_context = ""
        if is_modification:
            project_context = self._load_project_context_scoped(scope, mode)

        # ─── FASE 1: GENERACIÓN ───
        if self.crew_available:
            print(f"[ARCHITECT] Fase 1: Iniciando CrewAI...")
            set_all_status("working")
            try:
                crew_code, qa_report = run_ecommerce_workflow(user_prompt, project_context, is_modification)
                if not crew_code or crew_code.isspace():
                    raise ValueError("El flujo CrewAI no generó código.")
                set_all_status("done")
                print("[ARCHITECT] Generación de código completada.")
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

        # Guardar project.json si no fue generado
        project_json_path = Path(self.workspace_path) / "project.json"
        if not project_json_path.exists():
            project_json_path.write_text(json.dumps({
                "name": final_project_id,
                "created": datetime.now().isoformat()
            }, indent=2), encoding='utf-8')

        # ─── FASE 2.1: VALIDACIÓN DE INTEGRACIÓN ───
        self._validate_integration()

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

        # ─── FASE 3: REPARACIÓN AUTOMÁTICA ITERATIVA ───
        if qa_report and "No se ejecutó QA" not in qa_report and self.crew_available:
            for iteration in range(3):
                print(f"[ARCHITECT] Reparación iterativa {iteration+1}...")
                set_agent_status("Repair Agent", "working")
                try:
                    repair_prompt = f"""
CORRIGE el siguiente código según el informe de auditoría.
Devuelve el código corregido usando EXACTAMENTE el mismo formato (ruta:::código para cada archivo).
No añadas explicaciones, solo el código corregido.

INFORME DE AUDITORÍA:
{qa_report}

CÓDIGO ORIGINAL:
{crew_code}
"""
                    repaired_code = repair_agent.kickoff(repair_prompt)

                    if repaired_code and not str(repaired_code).isspace():
                        repaired_text = repaired_code.raw if hasattr(repaired_code, 'raw') else str(repaired_code)
                        if repaired_text and not repaired_text.isspace():
                            execute_plan(repaired_text, workspace_base=Path(self.workspace_path))
                            crew_code = repaired_text
                            print("[ARCHITECT] Código reparado aplicado.")
                            set_agent_status("Repair Agent", "done")
                            
                            # Revalidar integración después de reparar
                            self._validate_integration()
                except Exception as e:
                    set_agent_status("Repair Agent", "error")
                    print(f"[ARCHITECT] Error en reparación: {e}")

                if "error" not in qa_report.lower() and "vulnerabilidad" not in qa_report.lower():
                    print("[ARCHITECT] QA limpio. Fin de las reparaciones.")
                    break

        # ─── FASE 4: ANÁLISIS Y EJECUCIÓN ───
        try:
            print("[ARCHITECT] Escaneando estructura del proyecto...")
            self.memory.scan_project()
            initial_issues = self.memory.validate()
            if initial_issues:
                print(f"[ARCHITECT] {len(initial_issues)} problemas encontrados. Reparando...")
                self.memory.fix_imports_globally()

            print("[ARCHITECT] Ejecutando motor de refactorización...")
            refactor_log = self.refactor.analyze_and_fix(extended=True)
            if refactor_log:
                print(f"[ARCHITECT] {len(refactor_log)} mejoras sugeridas.")
                self.memory.scan_project()

            print("[ARCHITECT] Ejecutando proyecto...")
            executor = ProjectExecutor(str(self.workspace_path), memory=self.memory)
            execution_result = executor.execute_project()
            runtime_fix_log = execution_result.get('auto_fix_applied', [])

            # MetaAgent
            meta_proposals = 0
            try:
                print("[ARCHITECT] MetaAgent analizando el sistema...")
                meta = MetaAgent(memory=self.memory, queue=self.improvement_queue)
                proposal_ids = meta.analyze_and_propose(project_root=".")
                meta_proposals = len(proposal_ids)
                if meta_proposals > 0:
                    print(f"[ARCHITECT] MetaAgent generó {meta_proposals} propuestas.")
            except Exception as e:
                print(f"[ARCHITECT] MetaAgent error: {e}")

            # Contexto global
            try:
                context_summary = self.context.summary()
            except:
                context_summary = {"models": "N/A", "routes": "N/A", "entities": "N/A"}

            final_issues = self.memory.validate()
            success = execution_result.get('success', False)
            status = "✅ SALUDABLE" if success and not final_issues else "⚠️ REQUIERE ATENCIÓN"
            status += " (Ejecución exitosa)" if success else " (Falló la ejecución)"

            static_repairs = "\n".join([f"  - {r.get('action','')} en {r.get('file','')}" for r in fix_log_static]) if initial_issues else "Ninguna"
            runtime_repairs = "\n".join([f"  - {r.get('action','')} en {r.get('file','')}" for r in runtime_fix_log]) or "Ninguna"
            refactor_summary = "\n".join([f"  - {r.get('rule','')}: {r.get('file','')} ({r.get('suggestion','')})" for r in refactor_log]) or "Ninguna"

            report = "==================================================\n"
            report += "🧠 AUTONOMOUS SOFTWARE ARCHITECT REPORT\n"
            report += "==================================================\n"
            report += "ESTADO: " + str(status) + "\n\n"
            report += "1. REPARACIONES ESTÁTICAS:\n" + str(static_repairs) + "\n\n"
            report += "2. REFACTORIZACIONES APLICADAS:\n" + str(refactor_summary) + "\n\n"
            report += "3. EJECUCIÓN:\n"
            report += "   - Tipo: " + str(execution_result.get('execution_type', 'desconocido')) + "\n"
            report += "   - Éxito: " + str(success) + "\n"
            report += "   - Salida: " + str(execution_result.get('stdout', ''))[:200] + "\n"
            report += "   - Error: " + str(execution_result.get('stderr', ''))[:200] + "\n\n"
            report += "4. REPARACIONES EN RUNTIME:\n" + str(runtime_repairs) + "\n\n"
            report += "5. PROBLEMAS RESTANTES: " + str(len(final_issues) if final_issues else '0') + "\n\n"
            report += "6. CONTEXTO GLOBAL:\n"
            report += "   - Modelos: " + str(context_summary.get('models', '')) + "\n"
            report += "   - Rutas: " + str(context_summary.get('routes', '')) + "\n"
            report += "   - Entidades: " + str(context_summary.get('entities', '')) + "\n\n"
            report += "7. INFORME DE QA:\n" + qa_report[:500] + "\n"

            return report

        except Exception as e:
            error_report = "==================================================\n"
            error_report += "🧠 AUTONOMOUS SOFTWARE ARCHITECT REPORT (ERROR)\n"
            error_report += "==================================================\n"
            error_report += f"❌ Error en fase de ejecución/reparación: {str(e)}\n\n"
            error_report += traceback.format_exc()
            return error_report

    # ─── VALIDACIÓN DE INTEGRACIÓN ───
    def _validate_integration(self):
        backend_path = Path(self.workspace_path) / "backend"
        if not backend_path.exists():
            return
        
        main_file = backend_path / "main.py"
        if not main_file.exists():
            print("[ARCHITECT] ⚠️ No se encontró main.py, no se puede validar integración.")
            return

        main_content = main_file.read_text(encoding='utf-8')
        
        # Buscar todos los routers declarados en main.py
        import_pattern = r"app\.include_router\((\w+)\.router\)"
        imported_routers = set(re.findall(import_pattern, main_content))
        
        # Buscar todos los archivos .py en routers/ o en raíz que parezcan routers (tienen APIRouter)
        existing_routers = set()
        for py_file in backend_path.rglob("*.py"):
            if py_file.name == "__init__.py" or py_file.name == "main.py":
                continue
            try:
                content = py_file.read_text(encoding='utf-8')
                if "APIRouter" in content and "include_router" not in content:
                    router_name = py_file.stem
                    existing_routers.add(router_name)
            except:
                pass

        missing_integrations = existing_routers - imported_routers
        if missing_integrations:
            print(f"[ARCHITECT] ⚠️ Faltan integraciones en main.py: {missing_integrations}")
            repair_prompt = f"""
The following routers are defined but NOT included in main.py: {', '.join(missing_integrations)}.
Please provide ONLY the corrected main.py in format backend/main.py:::<code>.
Add the necessary import and app.include_router for each missing router.
Current main.py:
{main_content}
"""
            try:
                repaired = repair_agent.kickoff(repair_prompt)
                if repaired:
                    code = repaired.raw if hasattr(repaired, 'raw') else str(repaired)
                    if ":::" in code:
                        execute_plan(code, workspace_base=Path(self.workspace_path))
                        print("[ARCHITECT] ✅ main.py corregido automáticamente.")
            except Exception as e:
                print(f"[ARCHITECT] Error al corregir integración: {e}")

    # ─── MÉTODOS DE SOPORTE ───
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
                        content = f.read_text(encoding='utf-8')[:1000]
                        lines.append(f"=== {rel} ===\n{content}")
                    except:
                        lines.append(f"=== {rel} ===\n[binario]")
        return "\n".join(lines)

    def _save_project_context(self):
        context_path = Path(self.workspace_path) / "project_context.json"
        try:
            files = {}
            for f in Path(self.workspace_path).rglob("*"):
                if f.is_file() and f.name not in ["project_context.json", "chat.json"]:
                    rel = str(f.relative_to(self.workspace_path))
                    try:
                        files[rel] = f.read_text(encoding='utf-8')[:500]
                    except:
                        files[rel] = "[binario]"
            context_path.write_text(json.dumps({
                "files": list(files.keys()),
                "structure": {str(k): v for k, v in files.items()}
            }, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"[ARCHITECT] Error guardando contexto: {e}")

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
Genera o repara los archivos de dependencias para el siguiente {project_type}:
Archivos existentes: {', '.join(code_files[:10])}
Entrega usando el formato path:::code.
"""
        try:
            response = dependency_agent.kickoff(prompt)
            if response:
                dep_code = response.raw if hasattr(response, 'raw') else str(response)
                if dep_code:
                    execute_plan(dep_code, workspace_base=Path(self.workspace_path))
                    print(f"[ARCHITECT] Dependencias de {project_type} actualizadas.")
        except Exception as e:
            print(f"[ARCHITECT] Error al generar dependencias para {project_type}: {e}")

    def _generate_demo_plan(self, prompt):
        return (
            'backend/main.py:::from fastapi import FastAPI\n'
            'app = FastAPI()\n\n'
            '@app.get("/")\n'
            'def root():\n'
            '    return {"message": "Hello World"}\n'
        )