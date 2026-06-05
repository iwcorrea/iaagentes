from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path


class BaseAgent(ABC):
    """
    Interfaz común para todos los agentes del ecosistema.
    """

    def __init__(self, name: str, capabilities: List[str], memory: Optional[Any] = None):
        self.name = name
        self.capabilities = capabilities  # e.g., ["code_review", "refactor", "test"]
        self.memory = memory

    @abstractmethod
    def analyze(self, target: Path) -> List[Dict[str, Any]]:
        """
        Analiza un recurso (archivo, módulo) y devuelve hallazgos.
        Retorna lista de dicts: {"type": "...", "message": "...", "severity": "...", ...}
        """
        ...

    @abstractmethod
    def suggest_improvements(self, target: Path) -> List[str]:
        """
        Devuelve sugerencias textuales para mejorar el código/módulo.
        """
        ...

    def __repr__(self):
        return f"<Agent: {self.name} [{', '.join(self.capabilities)}]>"