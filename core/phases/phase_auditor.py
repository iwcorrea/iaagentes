"""
Fase 2: Auditoría y revisión de código.
Registra issues estructurados en ProjectMemory.
"""
from pathlib import Path
from typing import Dict, Any

from crewai import Agent, Task, Crew
from core.agent_cache import AgentCache
from core.project_memory import ProjectMemory


class PhaseAuditor:
    def __init__(self, workspace_path: Path, agent_cache: AgentCache, memory: ProjectMemory):
        self.workspace_path = workspace_path
        self.agent_cache = agent_cache
        self.memory = memory

    def execute(self) -> Dict[str, Any]:
        auditor = self.agent_cache.get_or_create(
            "auditor",
            lambda: Agent(
                role="Auditor de Código",
                goal="Revisar los archivos del proyecto en busca de errores de sintaxis, malas prácticas y posibles mejoras.",
                backstory="Eres un revisor de código meticuloso con experiencia en Python y React.",
                verbose=True,
                allow_delegation=False,
            )
        )

        manifest = self.memory.get_manifest_summary()
        task = Task(
            description=(
                f"Revisa los archivos listados a continuación.\n{manifest}\n\n"
                "Para cada archivo, indica si tiene errores de sintaxis, imports faltantes o incoherencias. "
                "Responde con un JSON que contenga una lista de issues con el formato:\n"
                '{"issues": [{"file": "ruta", "line": número, "message": "descripción", "severity": "warning|error"}]}\n'
                "Si no hay issues, responde: {'issues': []}"
            ),
            agent=auditor,
            expected_output="JSON con lista de issues."
        )

        crew = Crew(agents=[auditor], tasks=[task], verbose=True)
        crew.kickoff()

        raw = task.output.raw if hasattr(task.output, 'raw') else str(task.output)
        issues = self._extract_issues(raw)

        for issue in issues:
            self.memory.add_audit_issue(
                file=issue.get("file", ""),
                line=issue.get("line", 0),
                message=issue.get("message", ""),
                severity=issue.get("severity", "warning")
            )

        print(f"📋 Issues encontrados: {len(issues)}")
        return {"issues_found": len(issues)}

    def _extract_issues(self, raw: str) -> list:
        import json, re
        try:
            data = json.loads(raw)
            return data.get("issues", [])
        except:
            match = re.search(r'\{.*"issues".*\}', raw, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                    return data.get("issues", [])
                except:
                    pass
            return []