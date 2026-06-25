"""
Fase 2: Auditoría y revisión de código.
Revisa sintaxis y coherencia de los archivos generados.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

from crewai import Agent, Task, Crew
from core.agent_cache import AgentCache


class PhaseAuditor:
    def __init__(self, workspace_path: Path, agent_cache: AgentCache):
        self.workspace_path = workspace_path
        self.agent_cache = agent_cache

    def execute(self, manifest_context: str = "") -> Dict[str, Any]:
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

        task = Task(
            description=(
                f"Revisa los archivos listados a continuación.\n{manifest_context}\n\n"
                "Para cada archivo, indica si tiene errores de sintaxis, imports faltantes o incoherencias. "
                "Si todo está bien, responde 'AUDITORÍA APROBADA'. Si hay problemas, enuméralos brevemente."
            ),
            agent=auditor,
            expected_output="Resultado de la auditoría (texto)."
        )

        crew = Crew(agents=[auditor], tasks=[task], verbose=True)
        result = crew.kickoff()
        print("📋 Resultado de auditoría:", str(result)[:200])
        return {"audit_result": str(result)}