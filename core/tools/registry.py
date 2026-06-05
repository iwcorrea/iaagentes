from typing import List, Optional
from core.tools.base_tool import BaseTool


class ToolRegistry:
    """
    Registro central de herramientas disponibles.
    Los agentes y el motor de refactorización consultan este registro.
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools_by_capability(self, capability: str) -> List[BaseTool]:
        return [t for t in self._tools.values() if capability in t.capabilities]

    def list_all(self) -> List[str]:
        return list(self._tools.keys())