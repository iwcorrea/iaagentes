import sys
import ctypes
import importlib
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    def prevent_sleep():
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
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
from core.executor import execute_plan
from core.refactor_engine import RefactorEngine
from core.agents.registry import AgentRegistry
from core.simulated_agents import CodeAgent
from core.improvement_queue import ImprovementQueue
from core.meta_agent import MetaAgent
from core.prompt_integrity import PromptIntegrity
from core.agent_status import set_all_status, set_progress

# Fases modulares
from core.phases.phase_generator import PhaseGenerator
from core.phases.phase_auditor import PhaseAuditor
from core.phases.phase_dependencies import PhaseDependencies
from core.phases.phase_deploy import PhaseDeploy
from core.phases.phase_repair import PhaseRepair

CREWAI_AVAILABLE = True


class AutonomousArchitectOrchestrator:
    def __init__(self, workspace_path="workspace"):
        self.workspace_path = workspace_path
        self.memory = ArchitectureMemory(root_path=str(Path(workspace_path) / "backend"))
        self.context = GlobalContext()
        self.refactor = RefactorEngine(self.memory)
        self.agent_registry = AgentRegistry()
        self.agent_registry.register(CodeAgent(memory=self.memory))
        self.crew_available = CREWAI_AVAILABLE
        self.improvement_queue = ImprovementQueue()
        self.generated_files = []
        self.rate_limit_hits = 0

    def orchestrate_project(self, user_prompt: str, is_modification: bool = False,
                            scope: str = "all", mode: str = "full", turbo: bool = False) -> str:
        prevent_sleep()
        self.generated_files = []
        self.rate_limit_hits = 0
        try:
            # Validar prompt
            validator = PromptIntegrity()
            validation = validator.validate(user_prompt)
            if not validation["valid"]:
                user_prompt = validator.build_improved_prompt(user_prompt)
            set_progress(5)

            final_project_id = Path(self.workspace_path).name

            # Fase 1: Generación
            gen = PhaseGenerator(self)
            crew_code, qa_report = gen.run(user_prompt, is_modification, scope, mode, turbo)

            # Guardar metadatos del proyecto
            project_json = Path(self.workspace_path) / "project.json"
            if not project_json.exists():
                import json
                project_json.write_text(json.dumps({
                    "name": final_project_id,
                    "created": datetime.now().isoformat()
                }, indent=2), encoding='utf-8')

            # Fase 2: Auditoría
            aud = PhaseAuditor(self)
            aud.run(turbo)

            # Fase 3: Dependencias
            dep = PhaseDependencies(self)
            dep.run()

            # Fase 4: Despliegue y tests
            deploy = PhaseDeploy(self)
            deploy.run(turbo)

            # Fase 5: Reparación iterativa
            rep = PhaseRepair(self)
            rep.run(crew_code, qa_report, turbo)

            # Ejecución y MetaAgent
            self.memory.scan_project()
            self.memory.fix_imports_globally()
            self.refactor.analyze_and_fix(extended=True)

            from core.executor import ProjectExecutor
            executor = ProjectExecutor(str(self.workspace_path), memory=self.memory)
            execution_result = executor.execute_project()
            try:
                MetaAgent(memory=self.memory, queue=self.improvement_queue).analyze_and_propose(project_root=".")
            except:
                pass

            # Rastreador de aprendizaje
            from core.learning_tracker import LearningTracker
            tracker = LearningTracker()
            tracker.add_project(final_project_id, {
                "files": self.generated_files,
                "errors": [],
                "model_used": os.getenv("CURRENT_BRAIN_MODEL", "unknown"),
            })

            success = execution_result.get('success', False)
            status = "✅ SALUDABLE" if success else "⚠️ REQUIERE ATENCIÓN"
            report = f"🧠 PROYECTO {final_project_id}\nESTADO: {status}\nQA: {qa_report[:200] if not turbo else 'Turbo: QA omitido'}"
            if self.generated_files:
                report += f"\n📁 Archivos generados: {len(self.generated_files)}"
            set_all_status("done", "Proyecto completado")
            set_progress(100)
            return report
        finally:
            allow_sleep()