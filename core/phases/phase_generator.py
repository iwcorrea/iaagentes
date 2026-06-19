import sys
import importlib
import time
from pathlib import Path
from core.agent_status import set_agent_status, set_progress
from core.executor import execute_plan

MAX_RATE_LIMIT_RETRIES = 3

class PhaseGenerator:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def _get_agents(self):
        importlib.reload(sys.modules.get("agents.director_agent", None) or importlib.import_module("agents.director_agent"))
        importlib.reload(sys.modules.get("agents.backend_agent", None) or importlib.import_module("agents.backend_agent"))
        importlib.reload(sys.modules.get("agents.frontend_agent", None) or importlib.import_module("agents.frontend_agent"))
        importlib.reload(sys.modules.get("agents.qa_agent", None) or importlib.import_module("agents.qa_agent"))

        from agents.director_agent import director_agent
        from agents.backend_agent import backend_agent
        from agents.frontend_agent import frontend_agent
        from agents.qa_agent import qa_agent

        return director_agent, backend_agent, frontend_agent, qa_agent

    def run(self, user_prompt, is_modification, scope, mode, turbo):
        director_agent, backend_agent, frontend_agent, qa_agent = self._get_agents()

        set_agent_status("Director IA", "working", "Planificando estructura de archivos...")
        set_progress(10)

        project_context = ""
        if is_modification:
            project_context = self.orchestrator._load_project_context_scoped(scope, mode)

        if self.orchestrator.crew_available:
            try:
                from workflows.ecommerce_workflow import run_ecommerce_workflow
                crew_code, qa_report = run_ecommerce_workflow(user_prompt, project_context, is_modification)
                if crew_code:
                    self._save_incremental(crew_code)
                set_agent_status("Director IA", "done", "Plan completado")
                set_agent_status("Code Generator", "done", "Backend generado")
                set_agent_status("Frontend Designer", "done", "Frontend generado")
                set_progress(30)
                return crew_code, qa_report
            except Exception as e:
                if self._is_rate_limited(str(e)):
                    self.orchestrator.rate_limit_hits += 1
                    return self._generate_demo_plan(), "Rate limit"
                return self._generate_demo_plan(), "Error"
        return self._generate_demo_plan(), "CrewAI desactivado"

    def _save_incremental(self, crew_code):
        execute_plan(crew_code, workspace_base=Path(self.orchestrator.workspace_path))
        for f in Path(self.orchestrator.workspace_path).rglob("*"):
            if f.is_file():
                rel = str(f.relative_to(self.orchestrator.workspace_path))
                if rel not in self.orchestrator.generated_files:
                    self.orchestrator.generated_files.append(rel)

    def _generate_demo_plan(self):
        return 'backend/main.py:::from fastapi import FastAPI\napp = FastAPI()\n\n@app.get("/")\ndef root():\n    return {"message": "Hello World"}\n'

    def _is_rate_limited(self, msg):
        return "429" in msg or "Rate limit" in msg