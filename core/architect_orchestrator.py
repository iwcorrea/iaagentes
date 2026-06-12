import sys
import traceback
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

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
    """
    Orquestador profesional del ecosistema de agentes IA.
    Coordina generación, validación, reparación y despliegue de proyectos.
    """

    def __init__(self, workspace_path: str = "workspace"):
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

        # Métricas de rendimiento
        self.metrics: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "phases_completed": [],
            "tokens_estimated": 0,
            "repairs_applied": 0
        }

    def _log(self, message: str, level: str = "INFO") -> None:
        """Logging estructurado con timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "📘",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "PHASE": "🔄"
        }.get(level, "•")
        print(f"[{timestamp}] {prefix} {message}")

    def orchestrate_project(
        self,
        user_prompt: str,
        is_modification: bool = False,
        scope: str = "all",
        mode: str = "full"
    ) -> str:
        """
        Orquesta el flujo completo de generación de software.
        """
        self.metrics["start_time"] = datetime.now()
        crew_code = ""
        qa_report = ""
        final_project_id = Path(self.workspace_path).name

        # Cargar contexto para modificaciones
        project_context = ""
        if is_modification:
            self._log("Modo modificación activado", "PHASE")
            project_context = self._load_project_context_scoped(scope, mode)
            self._log(f"Contexto cargado: {len(project_context)} caracteres", "INFO")

        # ─── FASE 1: GENERACIÓN ───
        self._log("Fase 1: Generación de código", "PHASE")
        if self.crew_available:
            try:
                crew_code, qa_report = run_ecommerce_workflow(user_prompt, project_context, is_modification)
                if not crew_code or crew_code.isspace():
                    raise ValueError("El flujo CrewAI no generó código")
                self._log("Generación de código completada", "SUCCESS")
                self.metrics["phases_completed"].append("generation")
            except Exception as e:
                self._log(f"Fallo en generación: {e}", "ERROR")
                crew_code = self._generate_demo_plan(user_prompt)
                qa_report = "No se ejecutó QA (plan DEMO)"
                self._log("Usando plan DEMO como fallback", "WARNING")
        else:
            self._log("CrewAI no disponible, usando plan DEMO", "WARNING")
            crew_code = self._generate_demo_plan(user_prompt)
            qa_report = "CrewAI desactivado"

        # ─── FASE 2: ESCRITURA DE ARCHIVOS ───
        self._log("Fase 2: Escritura de archivos", "PHASE")
        try:
            execution_summary = execute_plan(crew_code, workspace_base=Path(self.workspace_path))
            self._log("Archivos escritos correctamente", "SUCCESS")
            self.metrics["phases_completed"].append("file_writing")
        except Exception as e:
            self._log(f"Error escribiendo archivos: {e}", "ERROR")

        # Guardar metadata del proyecto
        project_json_path = Path(self.workspace_path) / "project.json"
        if not project_json_path.exists():
            project_json_path.write_text(json.dumps({
                "name": final_project_id,
                "created": datetime.now().isoformat()
            }, indent=2), encoding='utf-8')

        self._save_project_context()

        # ─── FASE 3: GESTIÓN DE DEPENDENCIAS ───
        self._log("Fase 3: Verificación de dependencias", "PHASE")
        try:
            self._ensure_dependencies()
            self._log("Dependencias verificadas", "SUCCESS")
            self.metrics["phases_completed"].append("dependencies")
        except Exception as e:
            self._log(f"Error en dependencias: {e}", "WARNING")

        # ─── FASE 4: REPARACIÓN ITERATIVA ───
        if qa_report and "No se ejecutó QA" not in qa_report and self.crew_available:
            self._log("Fase 4: Reparación iterativa", "PHASE")
            repairs_applied = 0
            for iteration in range(3):
                self._log(f"Iteración {iteration + 1}/3", "INFO")
                try:
                    repair_prompt = f"""
CORRIGE el siguiente código según el informe de auditoría.
Devuelve EXACTAMENTE el formato ruta:::código para cada archivo.

INFORME DE AUDITORÍA:
{qa_report[:2000]}

CÓDIGO ORIGINAL:
{crew_code[:3000]}
"""
                    repaired_code = repair_agent.kickoff(repair_prompt)

                    if repaired_code and not str(repaired_code).isspace():
                        repaired_text = (
                            repaired_code.raw if hasattr(repaired_code, 'raw')
                            else str(repaired_code)
                        )
                        if repaired_text and not repaired_text.isspace():
                            execute_plan(repaired_text, workspace_base=Path(self.workspace_path))
                            crew_code = repaired_text
                            repairs_applied += 1

                            # Re-evaluar con QA
                            try:
                                qa_response = repair_agent.kickoff(
                                    f"Revisa y genera informe de auditoría:\n\n{repaired_text[:3000]}"
                                )
                                if qa_response and not str(qa_response).isspace():
                                    qa_report = (
                                        qa_response.raw if hasattr(qa_response, 'raw')
                                        else str(qa_response)
                                    )
                            except Exception:
                                pass

                            # Verificar si el código está limpio
                            if "error" not in qa_report.lower() and "vulnerabilidad" not in qa_report.lower():
                                self._log("Código limpio después de reparación", "SUCCESS")
                                break
                except Exception as e:
                    self._log(f"Error en reparación: {e}", "WARNING")

            self.metrics["repairs_applied"] = repairs_applied
            if repairs_applied > 0:
                self.metrics["phases_completed"].append("repair")

        # ─── FASE 5: ANÁLISIS FINAL Y EJECUCIÓN ───
        self._log("Fase 5: Análisis final y ejecución", "PHASE")
        try:
            self.memory.scan_project()
            initial_issues = self.memory.validate()
            if initial_issues:
                self._log(f"{len(initial_issues)} problemas encontrados", "WARNING")
                self.memory.fix_imports_globally()

            self.refactor.analyze_and_fix(extended=True)

            executor = ProjectExecutor(str(self.workspace_path), memory=self.memory)
            execution_result = executor.execute_project()
            success = execution_result.get('success', False)

            # Ejecutar MetaAgent
            try:
                meta = MetaAgent(memory=self.memory, queue=self.improvement_queue)
                proposal_ids = meta.analyze_and_propose(project_root=".")
                if proposal_ids:
                    self._log(f"MetaAgent generó {len(proposal_ids)} propuestas", "INFO")
            except Exception:
                pass

            final_issues = self.memory.validate()
            status = "✅ SALUDABLE" if success and not final_issues else "⚠️ REQUIERE ATENCIÓN"
            if success:
                status += " (Ejecución exitosa)"
            else:
                status += " (Falló la ejecución)"

            # Construir reporte
            report = self._build_report(
                status=status,
                execution_result=execution_result,
                qa_report=qa_report,
                metrics=self.metrics
            )

            self.metrics["end_time"] = datetime.now()
            elapsed = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()
            self._log(f"Orquestación completada en {elapsed:.1f}s", "SUCCESS")

            return report

        except Exception as e:
            self._log(f"Error en fase final: {e}", "ERROR")
            return self._build_error_report(e)

    def _build_report(
        self,
        status: str,
        execution_result: Dict,
        qa_report: str,
        metrics: Dict
    ) -> str:
        """Construye el reporte final de manera profesional."""
        try:
            context_summary = self.context.summary()
        except Exception:
            context_summary = {"models": "N/A", "routes": "N/A", "entities": "N/A"}

        elapsed = ""
        if metrics.get("start_time") and metrics.get("end_time"):
            elapsed = f"{(metrics['end_time'] - metrics['start_time']).total_seconds():.1f}s"

        return f"""
==================================================
🧠 REPORTE DEL ARQUITECTO AUTÓNOMO
==================================================
ESTADO: {status}
TIEMPO TOTAL: {elapsed}
FASES COMPLETADAS: {', '.join(metrics.get('phases_completed', []))}
REPARACIONES APLICADAS: {metrics.get('repairs_applied', 0)}

EJECUCIÓN:
  Tipo: {execution_result.get('execution_type', 'desconocido')}
  Éxito: {execution_result.get('success', False)}
  Salida: {execution_result.get('stdout', '')[:200]}
  Error: {execution_result.get('stderr', '')[:200]}

CONTEXTO GLOBAL:
  Modelos: {context_summary.get('models', '')}
  Rutas: {context_summary.get('routes', '')}
  Entidades: {context_summary.get('entities', '')}

INFORME DE QA:
{qa_report[:500] if qa_report else 'No disponible'}
"""

    def _build_error_report(self, exception: Exception) -> str:
        return f"""
==================================================
❌ ERROR EN ORQUESTACIÓN
==================================================
{str(exception)}

TRACEBACK:
{traceback.format_exc()[:1000]}
"""

    def _load_project_context_scoped(self, scope: str, mode: str) -> str:
        """Carga el contexto del proyecto según ámbito y modo."""
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
                    except Exception:
                        lines.append(f"=== {rel} ===\n[binario]")

        return "\n".join(lines)

    def _save_project_context(self) -> None:
        """Guarda el contexto del proyecto para futuras modificaciones."""
        context_path = Path(self.workspace_path) / "project_context.json"
        try:
            files = {}
            for f in Path(self.workspace_path).rglob("*"):
                if f.is_file() and f.name not in ["project_context.json", "chat.json"]:
                    rel = str(f.relative_to(self.workspace_path))
                    try:
                        files[rel] = f.read_text(encoding='utf-8')[:500]
                    except Exception:
                        files[rel] = "[binario]"
            context_path.write_text(json.dumps({
                "files": list(files.keys()),
                "structure": {str(k): v for k, v in files.items()}
            }, indent=2), encoding='utf-8')
        except Exception as e:
            self._log(f"Error guardando contexto: {e}", "WARNING")

    def _ensure_dependencies(self) -> None:
        """Verifica y repara dependencias del proyecto."""
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

    def _fix_dependencies(self, base_path: Path, project_type: str) -> None:
        """Usa el agente de dependencias para reparar archivos de configuración."""
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
                    self._log(f"Dependencias de {project_type} actualizadas", "SUCCESS")
        except Exception as e:
            self._log(f"Error generando dependencias: {e}", "WARNING")

    def _generate_demo_plan(self, prompt: str) -> str:
        """Plan de respaldo mínimo funcional."""
        return (
            'backend/main.py:::from fastapi import FastAPI\n'
            'app = FastAPI()\n\n'
            '@app.get("/")\n'
            'def root():\n'
            '    return {"message": "Hello World"}\n'
        )