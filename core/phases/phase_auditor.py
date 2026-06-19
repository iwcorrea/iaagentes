from core.agent_status import set_agent_status, set_progress
from core.project_auditor import ProjectAuditor
from core.code_reviewer import CodeReviewer
from core.syntax_validator import SyntaxValidator
from pathlib import Path

class PhaseAuditor:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def run(self, turbo):
        if self.orchestrator.rate_limit_hits >= 3:
            return

        # Project Auditor
        set_agent_status("QA Auditor", "working", "Revisando código generado...")
        prj_auditor = ProjectAuditor(self.orchestrator.workspace_path)
        issues = prj_auditor.audit()
        if issues:
            self._repair_issues(issues, turbo)

        # Code Reviewer
        set_agent_status("QA Auditor", "working", "Analizando estructura de código...")
        reviewer = CodeReviewer(self.orchestrator.workspace_path)
        review_issues = reviewer.review_backend()
        if review_issues:
            self._repair_issues(review_issues, turbo)

        # Syntax Validator
        validator = SyntaxValidator(self.orchestrator.workspace_path)
        syntax_errors = validator.validate_all()
        if syntax_errors:
            self._repair_issues(syntax_errors, turbo)

        set_agent_status("QA Auditor", "done", "Auditoría completada")
        set_progress(70)

    def _repair_issues(self, issues, turbo):
        if turbo or self.orchestrator.rate_limit_hits >= 3:
            return
        from agents.repair_agent import repair_agent
        prompt = f"Corrige:\n" + "\n".join(f"- {i}" for i in issues) + "\n\nFormato: ruta:::código."
        try:
            repaired = repair_agent.kickoff(prompt)
            if repaired:
                code = repaired.raw if hasattr(repaired, 'raw') else str(repaired)
                if ":::" in code:
                    from core.executor import execute_plan
                    execute_plan(code, workspace_base=Path(self.orchestrator.workspace_path))
        except Exception:
            pass