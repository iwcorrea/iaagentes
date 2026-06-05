import re
import ast
import hashlib
import copy
from pathlib import Path
from typing import List, Dict, Any
from core.architecture_memory import ArchitectureMemory, ModuleNode
from core.tools.registry import ToolRegistry
from core.tools.refactor_tools import (
    EnsurePackagesTool,
    FixProblematicRelativeImportsTool,
    LargeFileDetectorTool,
    OverloadedModuleDetectorTool,
    UnusedImportDetectorTool,
    DuplicateCodeDetectorTool,
)


class RefactorEngine:
    """
    Motor de refactorización basado en reglas.
    Ahora delegado en herramientas independientes registradas en un ToolRegistry.
    """

    def __init__(self, memory: ArchitectureMemory):
        self.memory = memory
        self.fix_log: List[Dict[str, Any]] = []
        # Inicializar el registro y cargar herramientas
        self.tool_registry = ToolRegistry()
        self._load_tools()

    def _load_tools(self):
        """Registra todas las herramientas disponibles."""
        self.tool_registry.register(EnsurePackagesTool())
        self.tool_registry.register(FixProblematicRelativeImportsTool())
        self.tool_registry.register(LargeFileDetectorTool(threshold=300))
        self.tool_registry.register(OverloadedModuleDetectorTool(threshold=5))
        self.tool_registry.register(UnusedImportDetectorTool())
        self.tool_registry.register(DuplicateCodeDetectorTool())  # extended

    def analyze_and_fix(self, extended: bool = False) -> List[Dict[str, Any]]:
        """
        Ejecuta todas las herramientas de refactorización disponibles.
        Si extended=True, también se ejecutan herramientas avanzadas (ej: duplicados).
        """
        self.fix_log.clear()

        # Determinar capacidades a ejecutar
        desired_caps = ["basic"]
        if extended:
            desired_caps.append("extended")

        for cap in desired_caps:
            tools = self.tool_registry.list_tools_by_capability(cap)
            for tool in tools:
                try:
                    result = tool.run(self.memory)
                    if result:
                        self.fix_log.extend(result)
                except Exception as e:
                    # Capturar errores de una herramienta sin detener el resto
                    self.fix_log.append({
                        'rule': 'tool_error',
                        'tool': tool.name,
                        'error': str(e),
                        'suggestion': 'Error ejecutando la herramienta.'
                    })

        return self.fix_log

    # Se conservan los métodos públicos por si otros componentes los llaman directamente,
    # pero ahora son atajos que delegan en las herramientas correspondientes.
    # (No es obligatorio, pero mantiene compatibilidad).