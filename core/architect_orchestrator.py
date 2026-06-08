import sys
import traceback
from pathlib import Path

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
from workflows.ecommerce_workflow import run_ecommerce_workflow
from agents.repair_agent import repair_agent

CREWAI_AVAILABLE = True


class AutonomousArchitectOrchestrator:
    def __init__(self, workspace_path="workspace"):
        self.workspace_path = workspace_path
        self.memory = ArchitectureMemory(root_path=str(Path(workspace_path) / "backend"))
        self.context = GlobalContext()
        self.refactor = RefactorEngine(self.memory)

        self.agent_registry = AgentRegistry()
        code_agent = CodeAgent(memory=self.memory)
        self.agent_registry.register(code_agent)

        self.crew_available = CREWAI_AVAILABLE
        self.improvement_queue = ImprovementQueue()

    def orchestrate_project(self, user_prompt: str) -> str:
        crew_code = ""
        qa_report = ""

        # ─── FASE 1: GENERACIÓN CON TODO EL CREW ───
        if self.crew_available:
            print("[ARCHITECT] Fase 1: Usando el flujo completo de agentes CrewAI.")
            try:
                crew_code, qa_report = run_ecommerce_workflow(user_prompt)
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

        # ─── FASE 2: ESCRITURA INICIAL DE ARCHIVOS ───
        execution_summary = execute_plan(crew_code, workspace_base=Path(self.workspace_path))

        # ─── FASE 3: REPARACIÓN AUTOMÁTICA ITERATIVA (hasta 2 rondas extra) ───
        if qa_report and "No se ejecutó QA" not in qa_report and self.crew_available:
            for iteration in range(2):
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
                        if hasattr(repaired_code, 'raw'):
                            repaired_text = repaired_code.raw
                        else:
                            repaired_text = str(repaired_code)

                        if repaired_text and not repaired_text.isspace():
                            print("[ARCHITECT] Código reparado recibido. Sobrescribiendo archivos...")
                            execute_plan(repaired_text, workspace_base=Path(self.workspace_path))
                            crew_code = repaired_text

                            # Volver a ejecutar QA sobre el código reparado para ver si mejoró
                            try:
                                from workflows.ecommerce_workflow import run_ecommerce_workflow
                                # Solo queremos el QA del nuevo código, no regenerar todo
                                qa_response = repair_agent.kickoff(
                                    f"Revisa el siguiente código y genera un informe de auditoría:\n\n{repaired_text}"
                                )
                                if qa_response and not str(qa_response).isspace():
                                    if hasattr(qa_response, 'raw'):
                                        qa_report = qa_response.raw
                                    else:
                                        qa_report = str(qa_response)
                                    print("[ARCHITECT] QA actualizado tras reparación.")
                            except Exception as qa_err:
                                print(f"[ARCHITECT] Error al re-ejecutar QA (no crítico): {qa_err}")

                            # Si el informe ya no contiene problemas graves, salir del bucle
                            if "error" not in qa_report.lower() and "vulnerabilidad" not in qa_report.lower():
                                print("[ARCHITECT] QA limpio. Reparación iterativa completada.")
                                break
                        else:
                            print("[ARCHITECT] La respuesta del Repair Agent está vacía.")
                    else:
                        print("[ARCHITECT] El Repair Agent no devolvió código válido.")
                except Exception as e:
                    print(f"[ARCHITECT] Error en reparación iterativa (no crítico): {e}")

        # ─── FASE 4: ANÁLISIS Y EJECUCIÓN ───
        try:
            print("[ARCHITECT] Escaneando estructura del proyecto...")
            self.memory.scan_project()
            initial_issues = self.memory.validate()
            fix_log_static = []
            if initial_issues:
                print(f"[ARCHITECT] {len(initial_issues)} problemas encontrados. Reparando...")
                fix_log_static = self.memory.fix_imports_globally()

            print("[ARCHITECT] Ejecutando motor de refactorización (extendido)...")
            refactor_log = self.refactor.analyze_and_fix(extended=True)
            if refactor_log:
                print(f"[ARCHITECT] {len(refactor_log)} mejoras sugeridas/aplicadas.")
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
                    print(f"[ARCHITECT] MetaAgent generó {meta_proposals} propuestas de mejora.")
            except Exception as e:
                print(f"[ARCHITECT] MetaAgent error (no crítico): {e}")

            try:
                context_summary = self.context.summary()
            except Exception:
                context_summary = {"models": "N/A", "routes": "N/A", "entities": "N/A"}

            final_issues = self.memory.validate()
            success = execution_result.get('success', False)
            status = "✅ SALUDABLE" if success and not final_issues else "⚠️ REQUIERE ATENCIÓN"
            status += " (Ejecución exitosa)" if success else " (Falló la ejecución)"

            static_repairs = "\n".join([f"  - {r.get('action','')} en {r.get('file','')}" for r in fix_log_static]) or "Ninguna"
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

    def _generate_demo_plan(self, prompt):
        """Plan DEMO que genera un pequeño proyecto FastAPI como fallback."""
        demo_code = (
            'backend/main.py:::from fastapi import FastAPI\n'
            'app = FastAPI()\n\n'
            '@app.get("/")\n'
            'def root():\n'
            '    return {"message": "Hello World"}\n'
        )
        return demo_code