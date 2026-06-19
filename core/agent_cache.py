"""
Cacheo de agentes CrewAI.
Evita recargar los agentes en cada solicitud si el modelo no cambió.
"""
import sys
from typing import Optional, Tuple

_cached_model: Optional[str] = None
_cached_agents: Optional[Tuple] = None

def get_agents(model: str):
    global _cached_model, _cached_agents
    if _cached_model == model and _cached_agents is not None:
        return _cached_agents

    import importlib
    importlib.reload(sys.modules.get("agents.director_agent", None) or importlib.import_module("agents.director_agent"))
    importlib.reload(sys.modules.get("agents.backend_agent", None) or importlib.import_module("agents.backend_agent"))
    importlib.reload(sys.modules.get("agents.frontend_agent", None) or importlib.import_module("agents.frontend_agent"))
    importlib.reload(sys.modules.get("agents.qa_agent", None) or importlib.import_module("agents.qa_agent"))
    importlib.reload(sys.modules.get("agents.repair_agent", None) or importlib.import_module("agents.repair_agent"))
    importlib.reload(sys.modules.get("agents.dependency_agent", None) or importlib.import_module("agents.dependency_agent"))

    from agents.director_agent import director_agent
    from agents.backend_agent import backend_agent
    from agents.frontend_agent import frontend_agent
    from agents.qa_agent import qa_agent
    from agents.repair_agent import repair_agent
    from agents.dependency_agent import dependency_agent

    _cached_model = model
    _cached_agents = (director_agent, backend_agent, frontend_agent, qa_agent, repair_agent, dependency_agent)
    return _cached_agents

def clear_cache():
    global _cached_model, _cached_agents
    _cached_model = None
    _cached_agents = None