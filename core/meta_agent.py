import ast
from pathlib import Path
from typing import List, Dict, Any
from core.architecture_memory import ArchitectureMemory
from core.improvement_queue import ImprovementQueue


class MetaAgent:
    """
    Agente que analiza el sistema y propone mejoras con código sugerido.
    Utiliza análisis estático avanzado (sin tokens).
    """

    def __init__(self, memory: ArchitectureMemory, queue: ImprovementQueue):
        self.memory = memory
        self.queue = queue

    def analyze_and_propose(self, project_root: str = ".") -> List[str]:
        ids = []
        core_path = Path(project_root) / "core"
        if core_path.exists():
            ids.extend(self._analyze_core_modules(core_path))
        ids.extend(self._analyze_from_memory())
        return ids

    def _analyze_core_modules(self, core_path: Path) -> List[str]:
        ids = []
        for py_file in core_path.rglob("*.py"):
            try:
                source = py_file.read_text(encoding='utf-8')
                tree = ast.parse(source)
                proposals = self._generate_proposals_from_file(py_file, tree)
                for prop in proposals:
                    proposal_id = self.queue.add_proposal(
                        agent_name="MetaAgent",
                        title=prop["title"],
                        description=prop["description"],
                        target_file=str(py_file.relative_to(Path.cwd())),
                        reason=prop["reason"],
                        suggested_code=prop.get("suggested_code", "")
                    )
                    ids.append(proposal_id)
            except:
                continue
        return ids

    def _generate_proposals_from_file(self, file_path: Path, tree) -> List[Dict]:
        proposals = []
        source = file_path.read_text(encoding='utf-8')

        for node in ast.walk(tree):
            # Funciones largas -> extraer en submódulos
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, 'end_lineno', node.lineno)
                length = end_line - node.lineno
                if length > 30:  # reduje umbral para pruebas
                    func_code = ast.get_source_segment(source, node)
                    if func_code:
                        new_module_code = self._extract_function_to_module(func_code, node.name, file_path.stem)
                        if new_module_code:
                            proposals.append({
                                "title": f"Extraer función larga '{node.name}' ({length} líneas)",
                                "description": f"La función '{node.name}' en {file_path.name} tiene {length} líneas. Se sugiere moverla a un módulo auxiliar.",
                                "reason": "Reduce complejidad y mejora legibilidad",
                                "suggested_code": new_module_code
                            })

            # Clases con muchos métodos -> sugerir división (sin código automático por ahora)
            if isinstance(node, ast.ClassDef):
                methods = [n for n in ast.iter_child_nodes(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                if len(methods) > 10:
                    proposals.append({
                        "title": f"Clase '{node.name}' con {len(methods)} métodos",
                        "description": f"La clase '{node.name}' en {file_path.name} tiene {len(methods)} métodos. Evalúa dividirla.",
                        "reason": "Principio de responsabilidad única",
                        "suggested_code": ""  # división compleja, se deja para IA
                    })

        # TODOs/FIXMEs
        for i, line in enumerate(source.splitlines(), 1):
            if "TODO" in line or "FIXME" in line:
                proposals.append({
                    "title": f"Pendiente en {file_path.name}:{i}",
                    "description": line.strip(),
                    "reason": "Tarea pendiente marcada en el código",
                    "suggested_code": ""
                })

        return proposals

    def _extract_function_to_module(self, func_code: str, func_name: str, module_name: str) -> str:
        """
        Genera el código de un nuevo módulo con la función extraída y las importaciones necesarias.
        Retorna el contenido del nuevo archivo .py.
        """
        lines = func_code.splitlines()
        header = lines[0]
        # Buscar imports dentro de la función (poco común) no se maneja aquí.
        # Simplemente copiamos la función y añadimos un comentario.
        new_module = f'"""\nMódulo auxiliar generado automáticamente para {func_name}\n"""\n\n'
        new_module += f'# Extraído de {module_name}.py\n'
        new_module += func_code
        return new_module

    def _analyze_from_memory(self) -> List[str]:
        ids = []
        issues = self.memory.validate()
        if issues:
            broken_count = len(issues)
            proposal_id = self.queue.add_proposal(
                agent_name="MetaAgent",
                title=f"Se detectaron {broken_count} imports rotos",
                description=f"La memoria arquitectónica encontró {broken_count} imports rotos.",
                target_file="workspace/backend",
                reason="Integridad del proyecto",
                suggested_code=""
            )
            ids.append(proposal_id)
        return ids