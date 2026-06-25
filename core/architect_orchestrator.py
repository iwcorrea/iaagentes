"""
Orquestador principal del ecosistema.
Utiliza ProjectMemory para persistencia, consultas rápidas y anti-alucinación.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from core.project_memory import ProjectMemory
from core.phases.phase_generator import PhaseGenerator
from core.phases.phase_auditor import PhaseAuditor
from core.phases.phase_dependencies import PhaseDependencies
from core.phases.phase_deploy import PhaseDeploy
from core.phases.phase_repair import PhaseRepair
from core.agent_cache import AgentCache
from core.project_context import ProjectContext


class AutonomousArchitectOrchestrator:
    def __init__(self, workspace_base: str = "generated_projects", workspace_path: str = None):
        if workspace_path:
            self.workspace_base = Path(workspace_path)
        else:
            self.workspace_base = Path(workspace_base)
        self.workspace_base.mkdir(exist_ok=True)
        self.agent_cache = AgentCache()
        self.project_context = ProjectContext()

    def orchestrate_project(
        self,
        user_prompt: str,
        project_name: str = None,
        model: str = None,
        is_modification: bool = False,
        scope: str = "all",
        mode: str = "full",
        turbo: bool = False
    ) -> str:
        if not project_name:
            project_name = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workspace_path = self.workspace_base / project_name
        workspace_path.mkdir(exist_ok=True)

        memory = ProjectMemory(str(workspace_path))
        memory.set_last_prompt(user_prompt)
        memory.set_model_used(model or os.getenv("CURRENT_BRAIN_MODEL", "unknown"))

        resume_phase = None
        if memory.is_phase_completed("generation"):
            resume_phase = "generation"
        if memory.is_phase_completed("audit"):
            resume_phase = "audit"
        if memory.is_phase_completed("dependencies"):
            resume_phase = "dependencies"
        if memory.is_phase_completed("tests"):
            resume_phase = "tests"
        if memory.is_phase_completed("deploy"):
            resume_phase = "deploy"

        print(f"📂 Proyecto: {project_name}")
        if resume_phase:
            print(f"⏯️  Reanudando desde fase: {resume_phase}")
        else:
            print("🚀 Iniciando generación completa...")

        # Fase 1: Generación
        if not resume_phase or resume_phase == "generation":
            try:
                print("\n📝 FASE 1: Generación de código")
                gen_phase = PhaseGenerator(workspace_path, self.agent_cache, memory)
                result = gen_phase.execute(user_prompt)

                files = result.get("files", {})
                if not files:
                    raise ValueError("El agente no generó ningún archivo válido.")

                for file_path, content in files.items():
                    self._save_incremental(workspace_path, file_path, content)
                    description = self._guess_file_description(file_path)
                    memory.add_file(file_path, content, description)

                memory.mark_phase_completed("generation")
                print(f"✅ Fase 1 completada ({len(files)} archivos)")
            except Exception as e:
                error_msg = f"Fase 1 (generación) falló: {str(e)}"
                memory.add_error(error_msg)
                return self._build_resume_message(workspace_path, "generation", str(e))

        # Fase 2: Auditoría
        if not resume_phase or resume_phase in ("generation", "audit"):
            try:
                print("\n🔍 FASE 2: Auditoría y revisión de código")
                audit_phase = PhaseAuditor(workspace_path, self.agent_cache, memory)
                audit_phase.execute()
                memory.mark_phase_completed("audit")
                print("✅ Fase 2 completada")
            except Exception as e:
                error_msg = f"Fase 2 (auditoría) falló: {str(e)}"
                memory.add_error(error_msg)
                return self._build_resume_message(workspace_path, "audit", str(e))

        # Fase 3: Dependencias
        if not resume_phase or resume_phase in ("generation", "audit", "dependencies"):
            try:
                print("\n📦 FASE 3: Instalación de dependencias")
                dep_phase = PhaseDependencies(workspace_path, self.agent_cache)
                dep_phase.execute(memory.get_manifest_summary())
                memory.set_dependencies_cached(True)
                memory.mark_phase_completed("dependencies")
                print("✅ Fase 3 completada")
            except Exception as e:
                error_msg = f"Fase 3 (dependencias) falló: {str(e)}"
                memory.add_error(error_msg)
                return self._build_resume_message(workspace_path, "dependencies", str(e))

        # Fase 4: Tests
        if not resume_phase or resume_phase in ("generation", "audit", "dependencies", "tests"):
            try:
                print("\n🧪 FASE 4: Generación de tests")
                deploy_phase = PhaseDeploy(workspace_path, self.agent_cache)
                result = deploy_phase.execute(memory.get_manifest_summary(), stage="tests")

                files = result.get("files", {})
                for file_path, content in files.items():
                    self._save_incremental(workspace_path, file_path, content)
                    memory.add_file(file_path, content, "Test unitario")

                memory.set_tests_generated(True)
                memory.mark_phase_completed("tests")
                print(f"✅ Fase 4 completada ({len(files)} archivos de tests)")
            except Exception as e:
                error_msg = f"Fase 4 (tests) falló: {str(e)}"
                memory.add_error(error_msg)
                return self._build_resume_message(workspace_path, "tests", str(e))

        # Fase 5: Despliegue
        if not resume_phase or resume_phase in ("generation", "audit", "dependencies", "tests", "deploy"):
            try:
                print("\n🚀 FASE 5: Despliegue y documentación")
                deploy_phase = PhaseDeploy(workspace_path, self.agent_cache)
                result = deploy_phase.execute(memory.get_manifest_summary(), stage="deploy")

                files = result.get("files", {})
                for file_path, content in files.items():
                    self._save_incremental(workspace_path, file_path, content)
                    memory.add_file(file_path, content, "Infraestructura / docs")

                memory.set_deploy_generated(True)
                memory.mark_phase_completed("deploy")
                print(f"✅ Fase 5 completada ({len(files)} archivos de despliegue)")
            except Exception as e:
                error_msg = f"Fase 5 (despliegue) falló: {str(e)}"
                memory.add_error(error_msg)
                return self._build_resume_message(workspace_path, "deploy", str(e))

        # Resumen final
        summary = (
            f"\n🎉 Proyecto completado. Archivos: {len(memory.to_dict()['files_manifest'])}\n"
            f"📂 Ubicación: {workspace_path}\n"
        )
        return summary

    def _save_incremental(self, workspace: Path, file_path: str, content: str):
        full_path = workspace / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')

    def _guess_file_description(self, file_path: str) -> str:
        path_lower = file_path.lower()
        if "main.py" in path_lower:
            return "Punto de entrada de la aplicación"
        elif "database" in path_lower:
            return "Configuración de la base de datos"
        elif "models/" in path_lower:
            return f"Modelo de datos: {Path(file_path).stem}"
        elif "schemas/" in path_lower:
            return f"Esquema Pydantic: {Path(file_path).stem}"
        elif "routers/" in path_lower or "routes/" in path_lower:
            return f"Router de API: {Path(file_path).stem}"
        elif "requirements.txt" in path_lower:
            return "Dependencias del proyecto"
        elif "dockerfile" in path_lower:
            return "Configuración de Docker"
        elif ".env" in path_lower:
            return "Variables de entorno"
        elif "readme" in path_lower:
            return "Documentación del proyecto"
        elif "test_" in path_lower:
            return f"Pruebas unitarias: {Path(file_path).stem}"
        elif file_path.endswith(".jsx") or file_path.endswith(".tsx"):
            return f"Componente React: {Path(file_path).stem}"
        elif file_path.endswith(".css"):
            return f"Estilos: {Path(file_path).stem}"
        return "Archivo de código"

    def _build_resume_message(self, workspace_path: Path, failed_phase: str, error_detail: str) -> str:
        return (
            f"⛔ La generación se detuvo en la fase '{failed_phase}'.\n\n"
            f"📋 Error: {error_detail}\n\n"
            f"📁 Proyecto guardado en: {workspace_path}\n"
            f"🔄 Podés reanudar más tarde enviando el mismo prompt (se continuará desde esta fase).\n"
            f"💡 Si el error es por rate‑limit, esperá a que se renueven los tokens gratuitos."
        )