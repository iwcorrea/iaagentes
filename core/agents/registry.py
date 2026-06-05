from typing import Dict, List, Optional
from core.agents.base_agent import BaseAgent


class AgentRegistry:
    """
    Mantiene un registro de agentes disponibles y permite consultarlos por capacidad.
    """

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._by_capability: Dict[str, List[BaseAgent]] = {}

    def register(self, agent: BaseAgent):
        self._agents[agent.name] = agent
        for cap in agent.capabilities:
            self._by_capability.setdefault(cap, []).append(agent)

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        return self._by_capability.get(capability, [])

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())