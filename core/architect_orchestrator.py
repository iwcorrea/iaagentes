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

        # Estado inicial
        set_all_status("idle")

        project_context = ""
        if is_modification:
            project_context = self._load_project_context_scoped(scope, mode)

        # ─── FASE 1: GENERACIÓN ───
        if self.crew_available:
            print(f"[ARCHITECT] Fase 1: Iniciando CrewAI...")
            set_all_status("working")  # Todos los agentes se ponen a trabajar
            try:
                crew_code, qa_report = run_ecommerce_workflow(user_prompt, project_context, is_modification)
                if not crew_code or crew_code.isspace():
                    raise ValueError("El flujo CrewAI no generó código.")
                set_all_status("done")  # Generación completada
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
                except Exception as e:
                    set_agent_status("Repair Agent", "error")
                    print(f"[ARCHITECT] Error en reparación: {e}")

                # Si el QA está limpio, salimos del bucle
                if "error" not in qa_report.lower() and "vulnerabilidad" not in qa_report.lower():
                    print("[ARCHITECT] QA limpio. Fin de las reparaciones.")
                    break

        # ─── FASE 4: ANÁLISIS Y EJECUCIÓN ───
        print("[ARCHITECT] Escaneando estructura...")
        self.memory.scan_project()
        print("[ARCHITECT] Ejecutando proyecto...")
        executor = ProjectExecutor(str(self.workspace_path), memory=self.memory)
        execution_result = executor.execute_project()

        # MetaAgent (opcional)
        try:
            print("[ARCHITECT] MetaAgent analizando...")
            meta = MetaAgent(memory=self.memory, queue=self.improvement_queue)
            meta.analyze_and_propose(project_root=".")
        except Exception as e:
            print(f"[ARCHITECT] MetaAgent error: {e}")

        # Reporte
        success = execution_result.get('success', False)
        status = "✅ SALUDABLE" if success else "⚠️ REQUIERE ATENCIÓN"
        report = f"""
🧠 PROYECTO {final_project_id}
ESTADO: {status}
SALIDA: {execution_result.get('stdout', '')[:200]}
ERROR: {execution_result.get('stderr', '')[:200]}
QA: {qa_report[:300]}
"""
        return report

    # ... (resto de métodos existentes sin cambios: _load_project_context_scoped, _ensure_dependencies, etc.) ...
    def _load_project_context_scoped(self, scope, mode):
        project_path = Path(self.workspace_path)
        lines = []
        for f in project_path.rglob("*"):
            if f.is_file() and f.name not in ["project_context.json", "chat.json"]:
                rel = str(f.relative_to(project_path))
                if scope == "backend" and not rel.startswith("backend"): continue
                if scope == "frontend" and not rel.startswith("frontend"): continue
                if mode == "light":
                    lines.append(f"- {rel}")
                else:
                    try: content = f.read_text(encoding='utf-8')[:1000]; lines.append(f"=== {rel} ===\n{content}")
                    except: pass
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

    def _fix_dependencies(self, base_path, project_type):
        code_files = [str(f.relative_to(base_path)) for ext in ['.py','.jsx','.js'] for f in base_path.rglob(f'*{ext}') if f.name not in ["requirements.txt","package.json"]]
        if not code_files: return
        prompt = f"Genera archivo de dependencias para {project_type} con archivos: {', '.join(code_files[:10])}. Usa formato path:::code."
        try:
            resp = dependency_agent.kickoff(prompt)
            if resp:
                code = resp.raw if hasattr(resp,'raw') else str(resp)
                if code: execute_plan(code, workspace_base=Path(self.workspace_path))
        except Exception as e: print(f"Error dependencias: {e}")

    def _save_project_context(self):
        pass

    def _generate_demo_plan(self, prompt):
        return 'backend/main.py:::from fastapi import FastAPI\napp = FastAPI()\n\n@app.get("/")\ndef root():\n    return {"message": "Hello World"}\n'