"""
Wrappers de agentes CrewAI para el ecosistema.
Cada clase hereda de BaseAgent y se comunica con el agente real definido en agents/.
"""

from pathlib import Path
from typing import List, Dict, Any
from core.agents.base_agent import BaseAgent
from agents.backend_agent import backend_agent
from agents.director_agent import director_agent
from agents.repair_agent import repair_agent
from agents.qa_agent import qa_agent
from agents.frontend_agent import frontend_agent


class CrewBackendAgent(BaseAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="crew_backend_agent",
            capabilities=["code_generation", "backend"],
            memory=memory
        )

    def analyze(self, target: Path) -> List[Dict[str, Any]]:
        # El backend agent genera código, no analiza archivos directamente
        return []

    def suggest_improvements(self, target: Path) -> List[str]:
        # Podría delegarse a una llamada específica, por ahora retornamos vacío
        return []


class CrewDirectorAgent(BaseAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="crew_director_agent",
            capabilities=["planning", "task_decomposition"],
            memory=memory
        )

    def analyze(self, target: Path) -> List[Dict[str, Any]]:
        return []

    def suggest_improvements(self, target: Path) -> List[str]:
        # Podría sugerir planes de mejora, se deja para la implementación futura
        return []


class CrewRepairAgent(BaseAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="crew_repair_agent",
            capabilities=["code_repair", "debugging"],
            memory=memory
        )

    def analyze(self, target: Path) -> List[Dict[str, Any]]:
        # Usaría repair_agent.kickoff? Por ahora solo devolvemos estructura
        return []

    def suggest_improvements(self, target: Path) -> List[str]:
        # Podría solicitar reparaciones automáticas si se detectan errores
        return []


class CrewQAAgent(BaseAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="crew_qa_agent",
            capabilities=["quality_assurance", "vulnerability_detection"],
            memory=memory
        )

    def analyze(self, target: Path) -> List[Dict[str, Any]]:
        return []

    def suggest_improvements(self, target: Path) -> List[str]:
        return []


class CrewFrontendAgent(BaseAgent):
    def __init__(self, memory=None):
        super().__init__(
            name="crew_frontend_agent",
            capabilities=["frontend_design", "react", "tailwind"],
            memory=memory
        )

    def analyze(self, target: Path) -> List[Dict[str, Any]]:
        return []

    def suggest_improvements(self, target: Path) -> List[str]:
        return []