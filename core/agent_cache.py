"""
Caché de agentes CrewAI.
Permite cargar agentes desde definiciones por defecto o desde skills externos.
Ahora consulta el SkillRegistry por nombre o por rol.
"""
from typing import Dict, Callable
from crewai import Agent
from core.skill_registry import SkillRegistry


class AgentCache:
    def __init__(self, skill_registry: SkillRegistry = None):
        self._cache: Dict[str, Agent] = {}
        self.skill_registry = skill_registry or SkillRegistry()

    def get_or_create(self, agent_name: str, default_factory: Callable[[], Agent],
                      agent_role: str = None) -> Agent:
        """
        Devuelve el agente cacheado. Si existe un skill que coincida con agent_name o agent_role,
        lo usa en lugar de la factory por defecto.
        """
        cache_key = agent_name
        if cache_key not in self._cache:
            # Intentar cargar desde skill
            skill = self.skill_registry.get_skill_by_name(agent_name)
            if not skill and agent_role:
                skill = self.skill_registry.get_skill_by_role(agent_role)
            if skill:
                self._cache[cache_key] = self._create_agent_from_skill(skill)
            else:
                self._cache[cache_key] = default_factory()
        return self._cache[cache_key]

    def _create_agent_from_skill(self, skill: dict) -> Agent:
        return Agent(
            role=skill.get("role", "Assistant"),
            goal=skill.get("goal", "Help the user"),
            backstory=skill.get("backstory", ""),
            tools=skill.get("tools", []),
            verbose=skill.get("verbose", True),
            allow_delegation=skill.get("allow_delegation", False),
        )

    def clear(self):
        self._cache.clear()


# Singleton para clear_cache
_cache_instance = AgentCache()

def clear_cache():
    _cache_instance.clear()