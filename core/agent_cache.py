"""
Caché de agentes CrewAI.
Proporciona una clase AgentCache y una función clear_cache
para limpiar la caché global de agentes.
"""
from typing import Dict, Callable
from crewai import Agent


class AgentCache:
    def __init__(self):
        self._cache: Dict[str, Agent] = {}

    def get_or_create(self, agent_name: str, factory: Callable[[], Agent]) -> Agent:
        """
        Devuelve el agente cacheado o lo crea usando la función factory.
        """
        if agent_name not in self._cache:
            self._cache[agent_name] = factory()
        return self._cache[agent_name]

    def clear(self):
        """Limpia la caché de agentes de esta instancia."""
        self._cache.clear()


# ------------------------------------------------------------------
# Singleton para importaciones directas de clear_cache
# ------------------------------------------------------------------
_cache_instance = AgentCache()


def clear_cache():
    """Limpia la caché global de agentes (singleton)."""
    _cache_instance.clear()