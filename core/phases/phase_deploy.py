from pathlib import Path
from core.agent_status import set_agent_status, set_progress

class PhaseDeploy:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def run(self, turbo):
        if turbo or self.orchestrator.rate_limit_hits >= 3:
            return

        # Tests
        set_agent_status("Test Generator", "working", "Generando tests unitarios...")
        try:
            from agents.test_agent import test_agent
            self._generate_tests(test_agent)
        except Exception:
            pass
        set_progress(92)

        # Despliegue y docs
        set_agent_status("Deploy Agent", "working", "Generando despliegue y documentación...")
        try:
            from agents.deploy_agent import deploy_agent
            self._generate_deploy(deploy_agent)
        except Exception:
            pass
        set_progress(96)

    def _generate_tests(self, agent):
        backend_path = Path(self.orchestrator.workspace_path) / "backend"
        if not backend_path.exists():
            return
        code_files = []
        for f in backend_path.rglob("*.py"):
            if f.name != "__init__.py":
                try:
                    code_files.append(f.read_text(encoding='utf-8')[:1500])
                except:
                    pass
        if code_files:
            prompt = f"Genera tests con pytest:\n{chr(10).join(code_files[:5])}\n\nFormato: ruta:::código."
            response = agent.kickoff(prompt)
            if response:
                code = response.raw if hasattr(response, 'raw') else str(response)
                if ":::" in code:
                    from core.executor import execute_plan
                    execute_plan(code, workspace_base=Path(self.orchestrator.workspace_path))

    def _generate_deploy(self, agent):
        backend_path = Path(self.orchestrator.workspace_path) / "backend"
        info = []
        if backend_path.exists():
            for f in backend_path.rglob("*.py"):
                if f.name != "__init__.py":
                    try:
                        info.append(f.read_text(encoding='utf-8')[:1000])
                    except:
                        pass
        prompt = f"Genera Dockerfile, docker-compose.yml, .env.example, README.md:\n{chr(10).join(info[:3])}\n\nFormato: ruta:::código."
        response = agent.kickoff(prompt)
        if response:
            code = response.raw if hasattr(response, 'raw') else str(response)
            if ":::" in code:
                from core.executor import execute_plan
                execute_plan(code, workspace_base=Path(self.orchestrator.workspace_path))