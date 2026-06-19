from core.agent_status import set_agent_status

class PhaseRepair:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def run(self, crew_code, qa_report, turbo):
        if turbo or not qa_report or "No se ejecutó QA" in qa_report:
            return
        if self.orchestrator.rate_limit_hits >= 3:
            return

        set_agent_status("Repair Agent", "working", "Aplicando correcciones...")
        for iteration in range(3):
            try:
                from agents.repair_agent import repair_agent
                reduced = self._reduce(crew_code)
                prompt = f"Corrige según auditoría:\n{qa_report[:500]}\n\nCódigo:\n{reduced}\n\nFormato: ruta:::código."
                repaired = repair_agent.kickoff(prompt)
                if repaired:
                    text = repaired.raw if hasattr(repaired, 'raw') else str(repaired)
                    if ":::" in text:
                        from core.executor import execute_plan
                        from pathlib import Path
                        execute_plan(text, workspace_base=Path(self.orchestrator.workspace_path))
                        crew_code = text
            except Exception as e:
                if "429" in str(e) or "Rate limit" in str(e):
                    self.orchestrator.rate_limit_hits += 1
                    break
        set_agent_status("Repair Agent", "done", "Reparaciones finalizadas")

    def _reduce(self, code):
        lines = code.split('\n')
        reduced = []
        for line in lines:
            if ':::' in line:
                parts = line.split(':::', 1)
                reduced.append(f"{parts[0]}:::")
                reduced.append('\n'.join(parts[1].split('\n')[:3]))
                reduced.append('...')
            else:
                reduced.append(line[:200])
        return '\n'.join(reduced[:50])