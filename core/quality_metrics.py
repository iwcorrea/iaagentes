import ast
from pathlib import Path
from typing import Dict, Any
from core.architecture_memory import ArchitectureMemory


def analyze_quality(project_path: str = "workspace/backend") -> Dict[str, Any]:
    """
    Calcula métricas de calidad del código Python en el proyecto.
    Devuelve un diccionario con las métricas globales y por archivo.
    """
    root = Path(project_path)
    metrics = {
        "total_files": 0,
        "total_lines": 0,
        "avg_complexity": 0.0,
        "docstring_coverage": 0.0,
        "broken_imports": 0,
        "files": []
    }

    memory = ArchitectureMemory(root_path=str(root))
    memory.scan_project()

    total_functions = 0
    total_complexity = 0
    total_with_docstring = 0
    broken_imports = len(memory.validate())

    for node in memory.nodes.values():
        if not node.path.suffix == '.py':
            continue
        try:
            source = node.path.read_text(encoding='utf-8')
            tree = ast.parse(source)
            lines = len(source.splitlines())
            functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            func_count = len(functions)
            complexity = sum(_cyclomatic_complexity(func) for func in functions)
            docstring_funcs = sum(1 for f in functions if _has_docstring(f))

            file_metrics = {
                "file": str(node.path.relative_to(root)),
                "lines": lines,
                "functions": func_count,
                "complexity": complexity,
                "docstring_funcs": docstring_funcs
            }
            metrics["files"].append(file_metrics)
            metrics["total_files"] += 1
            metrics["total_lines"] += lines
            total_functions += func_count
            total_complexity += complexity
            total_with_docstring += docstring_funcs
        except:
            continue

    if total_functions > 0:
        metrics["docstring_coverage"] = round((total_with_docstring / total_functions) * 100, 2)
        metrics["avg_complexity"] = round(total_complexity / total_functions, 2)
    metrics["broken_imports"] = broken_imports
    return metrics


def _cyclomatic_complexity(func_node) -> int:
    """Calcula complejidad ciclomática simple: 1 + número de ramas."""
    complexity = 1
    for node in ast.walk(func_node):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.And, ast.Or, ast.ExceptHandler)):
            complexity += 1
    return complexity


def _has_docstring(func_node) -> bool:
    """Verifica si una función tiene docstring."""
    return (func_node.body and isinstance(func_node.body[0], ast.Expr) and
            isinstance(func_node.body[0].value, ast.Constant) and
            isinstance(func_node.body[0].value.value, str))