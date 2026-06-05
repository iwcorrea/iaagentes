from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseTool(ABC):
    """
    Interfaz común para todas las herramientas del sistema.
    Cada herramienta tiene un nombre, descripción y capacidades.
    """

    def __init__(self, name: str, description: str, capabilities: List[str]):
        self.name = name
        self.description = description
        self.capabilities = capabilities  # e.g., ["basic", "extended", "analysis"]

    @abstractmethod
    def run(self, memory) -> List[Dict[str, Any]]:
        """
        Ejecuta la herramienta sobre la memoria arquitectónica.
        Devuelve una lista de registros de reparación/sugerencia.
        """
        ...