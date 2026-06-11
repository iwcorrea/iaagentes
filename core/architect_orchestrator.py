import sys
import traceback
import json
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

    def orchestrate_project(
        self,
        user_prompt: str,
        is_modification: bool = False,
        scope: str = "all",
        mode: str = "full"
    ) -> str:
        """
        Orquesta la generación o modificación de un proyecto.
        
        Args:
            user_prompt: El prompt del usuario.
            is_modification: Si se debe modificar un proyecto existente.
            scope: Ámbito de la modificación: 'backend', 'frontend' o 'all'.
            mode: Modo de contexto: 'full' (código completo) o 'light' (solo estructura).
        """
        crew_code = ""
        qa_report = ""
        final_project_id = Path(self.workspace_path).name

        # Cargar contexto según ámbito y modo
        project_context = ""
        if is_modification:
            project_context = self._load_project_context_scoped(scope, mode)
            print(f"[ARCHITECT] Modo modificación activado. Scope: {scope}, Mode: {mode}.")

        # ─── FASE 1: GENERACIÓN ───
        if self.crew_available:
            print(f"[ARCHITECT] Fase 1: Usando el flujo completo de agentes CrewAI.")
            try:
                crew_code, qa_report = run_ecommerce_workflow(user_prompt, project_context, is_modification)
                if not crew_code or crew_code.isspace():
                    raise ValueError("El flujo CrewAI no generó código.")
                print("[ARCHITECT] Generación de código completada.")
            except Exception as e:
                print(f"[ARCHITECT] Falló generación CrewAI: {e}. Usando plan DEMO.")
                crew_code = self._generate_demo_plan(user_prompt)
                qa_report = "No se ejecutó QA (plan DEMO)."
        else:
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

        self._save_project_context()

        # ─── FASE 2.5: GESTIÓN DE DEPENDENCIAS ───
        print("[ARCHITECT] Verificando dependencias...")
        try:
            self._ensure_dependencies()
        except Exception as e:
            print(f"[ARCHITECT] Error al asegurar dependencias: {e}")

        # ─── FASE 3: REPARACIÓN AUTOMÁTICA ITERATIVA ───
        if qa_report and "No se ejecutó QA" not in qa_report and self.crew_available:
            for iteration in range(3):
                print(f"[ARCHITECT] Fase 3 (iteración {iteration+1}): Reparando código basado en QA...")
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
                            print("[ARCHITECT] Código reparado recibido. Sobrescribiendo archivos...")
                            execute_plan(repaired_text, workspace_base=Path(self.workspace_path))
                            crew_code = repaired_text

                            try:
                                qa_response = repair_agent.kickoff(
                                    f"Revisa el siguiente código y genera un informe de auditoría:\n\n{repaired_text}"
                                )
                                if qa_response and not str(qa_response).isspace():
                                    qa_report = qa_response.raw if hasattr(qa_response, 'raw') else str(qa_response)
                                    print("[ARCHITECT] QA actualizado tras reparación.")
                            except Exception as qa_err:
                                print(f"[ARCHITECT] Error al re-ejecutar QA: {qa_err}")

                            if "error" not in qa_report.lower() and "vulnerabilidad" not in qa_report.lower():
                                print("[ARCHITECT] QA limpio. Reparación iterativa completada.")
                                break
                except Exception as e:
                    print(f"[ARCHITECT] Error en reparación iterativa: {e}")

        # ─── FASE 4: ANÁLISIS Y EJECUCIÓN ───
        try:
            print("[ARCHITECT] Escaneando estructura del proyecto...")
            self.memory.scan_project()
            initial_issues = self.memory.validate()
            fix_log_static = []
            if initial_issues:
                print(f"[ARCHITECT] {len(initial_issues)} problemas encontrados. Reparando...")
                fix_log_static = self.memory.fix_imports_globally()

            print("[ARCHITECT] Ejecutando motor de refactorización...")
            refactor_log = self.refactor.analyze_and_fix(extended=True)
            if refactor_log:
                self.memory.scan_project()

            print("[ARCHITECT] Ejecutando proyecto...")
            executor = ProjectExecutor(str(self.workspace_path), memory=self.memory)
            execution_result = executor.execute_project()
            runtime_fix_log = execution_result.get('auto_fix_applied', [])

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

            context_summary = {"models": "N/A", "routes": "N/A", "entities": "N/A"}
            try:
                context_summary = self.context.summary()
            except:
                pass

            final_issues = self.memory.validate()
            success = execution_result.get('success', False)
            status = "✅ SALUDABLE" if success and not final_issues else "⚠️ REQUIERE ATENCIÓN"
            status += " (Ejecución exitosa)" if success else " (Falló la ejecución)"

            report = "==================================================\n"
            report += "🧠 AUTONOMOUS SOFTWARE ARCHITECT REPORT\n"
            report += "==================================================\n"
            report += "ESTADO: " + status + "\n\n"
            report += "1. REPARACIONES ESTÁTICAS:\n" + "\n".join(
                [f"  - {r.get('action','')} en {r.get('file','')}" for r in fix_log_static]
            ) or "Ninguna" + "\n\n"
            report += "2. REFACTORIZACIONES:\n" + "\n".join(
                [f"  - {r.get('rule','')}: {r.get('file','')}" for r in refactor_log]
            ) or "Ninguna" + "\n\n"
            report += "3. EJECUCIÓN:\n"
            report += f"   - Tipo: {execution_result.get('execution_type', 'desconocido')}\n"
            report += f"   - Éxito: {success}\n"
            report += f"   - Salida: {execution_result.get('stdout', '')[:200]}\n"
            report += f"   - Error: {execution_result.get('stderr', '')[:200]}\n\n"
            report += "4. RUNTIME:\n" + "\n".join(
                [f"  - {r.get('action','')} en {r.get('file','')}" for r in runtime_fix_log]
            ) or "Ninguna" + "\n\n"
            report += f"5. PROBLEMAS RESTANTES: {len(final_issues) if final_issues else 0}\n\n"
            report += "6. CONTEXTO GLOBAL:\n"
            report += f"   - Modelos: {context_summary.get('models', '')}\n"
            report += f"   - Rutas: {context_summary.get('routes', '')}\n"
            report += f"   - Entidades: {context_summary.get('entities', '')}\n\n"
            report += "7. INFORME DE QA:\n" + qa_report[:500] + "\n"

            return report
        except Exception as e:
            return "ERROR:\n" + traceback.format_exc()

    def _load_project_context_scoped(self, scope: str, mode: str) -> str:
        """
        Carga el contexto según el ámbito (backend/frontend/all) y el modo (light/full).
        """
        project_path = Path(self.workspace_path)
        if not project_path.exists():
            return ""

        lines = []
        for f in project_path.rglob("*"):
            if f.is_file() and f.name not in ["project_context.json", "chat.json", "project.json"]:
                rel = str(f.relative_to(project_path))

                # Filtrar por ámbito
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
        except Exception as e:
            print(f"[ARCHITECT] Error generando dependencias: {e}")

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
            context_path.write_text(json.dumps({"files": list(files.keys()), "structure": files}, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"[ARCHITECT] Error guardando contexto: {e}")

    def _generate_demo_plan(self, prompt):
        return (
            'backend/main.py:::from fastapi import FastAPI\n'
            'app = FastAPI()\n\n'
            '@app.get("/")\n'
            'def root():\n'
            '    return {"message": "Hello World"}\n'
        )