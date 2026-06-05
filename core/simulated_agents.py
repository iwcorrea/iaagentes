# core/simulated_agents.py
"""
Agentes simulados que operan sin llamadas a LLM.
Proporcionan sugerencias deterministas basadas en análisis estático.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any
from core.agents.base_agent import BaseAgent


class CodeAgent(BaseAgent):
    """
    Simula un agente experto en código. Ofrece sugerencias simples (docstrings, complejidad).
    """

    def __init__(self, memory=None):
        super().__init__(
            name="simulated_code_agent",
            capabilities=["code_review", "style_check", "complexity_check"],
            memory=memory
        )

    def analyze(self, target: Path) -> List[Dict[str, Any]]:
        suggestions = self.suggest_improvements(target)
        findings = []
        for s in suggestions:
            findings.append({
                "type": "improvement",
                "file": str(target),
                "message": s,
                "severity": "info"
            })
        return findings

    def suggest_improvements(self, module_path: Path) -> List[str]:
        """Analiza un módulo Python y devuelve sugerencias textuales."""
        if not module_path.exists():
            return []
        try:
            source = module_path.read_text(encoding='utf-8')
        except Exception:
            return []
        tree = ast.parse(source)
        suggestions = []

        # 1. Funciones sin docstring
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not (node.body and isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant) and 
                        isinstance(node.body[0].value.value, str)):
                    suggestions.append(
                        f"[{module_path}:{node.lineno}] Función '{node.name}' sin docstring. "
                        "Considera documentarla."
                    )

        # 2. Anidamiento excesivo de if (>3)
        max_depth = self._max_nested_ifs(tree)
        if max_depth > 3:
            suggestions.append(
                f"[{module_path}] Profundidad máxima de if anidados: {max_depth}. "
                "Considera extraer lógica en funciones auxiliares."
            )

        # 3. Líneas muy largas (>120 caracteres)
        lines = source.splitlines()
        for i, line in enumerate(lines, start=1):
            if len(line) > 120:
                suggestions.append(
                    f"[{module_path}:{i}] Línea excesivamente larga ({len(line)} caracteres). Considera dividir."
                )
                if len(suggestions) >= 10:  # límite para no saturar
                    break

        return suggestions

    def _max_nested_ifs(self, node, depth=0):
        if isinstance(node, ast.If):
            depth += 1
            child_depths = [self._max_nested_ifs(c, depth) for c in ast.iter_child_nodes(node)]
            return max(child_depths, default=depth)
        else:
            return max([self._max_nested_ifs(c, depth) for c in ast.iter_child_nodes(node)], default=depth)