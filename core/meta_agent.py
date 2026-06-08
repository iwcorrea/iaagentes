import ast
from pathlib import Path
from typing import List, Dict, Any
from core.architecture_memory import ArchitectureMemory
from core.improvement_queue import ImprovementQueue

class MetaAgent:
    """
    Agente que analiza el sistema y propone mejoras con código sugerido.
    Utiliza análisis estático avanzado (sin tokens) y recurre al Repair Agent
    para generar código corregido cuando es necesario.
    """

    def __init__(self, memory: ArchitectureMemory, queue: ImprovementQueue):
        self.memory = memory
        self.queue = queue
        self.repair_agent = None  # Se inicializa bajo demanda para ahorrar recursos

    def _get_repair_agent(self):
        """Inicializa el Repair Agent solo cuando se necesita."""
        if self.repair_agent is None:
            try:
                from agents.repair_agent import repair_agent
                self.repair_agent = repair_agent
            except Exception as e:
                print(f"[MetaAgent] No se pudo cargar Repair Agent: {e}")
        return self.repair_agent

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
            # Funciones largas -> sugerir extracción con código generado por Repair Agent
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, 'end_lineno', node.lineno)
                length = end_line - node.lineno
                if length > 30:
                    func_code = ast.get_source_segment(source, node)
                    if func_code:
                        # Intentar obtener código refactorizado del Repair Agent
                        new_module_code = self._get_refactored_code(
                            file_path, node.name, func_code
                        )
                        proposals.append({
                            "title": f"Extraer función larga '{node.name}' ({length} líneas)",
                            "description": f"La función '{node.name}' en {file_path.name} tiene {length} líneas. Se sugiere moverla a un módulo auxiliar.",
                            "reason": "Reduce complejidad y mejora legibilidad",
                            "suggested_code": new_module_code if new_module_code else ""
                        })

            # Clases con muchos métodos -> sugerir división (con ayuda de Repair Agent)
            if isinstance(node, ast.ClassDef):
                methods = [n for n in ast.iter_child_nodes(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                if len(methods) > 10:
                    # Solo generamos código si el Repair Agent está disponible
                    repair_agent = self._get_repair_agent()
                    if repair_agent:
                        class_code = ast.get_source_segment(source, node)
                        if class_code:
                            prompt = f"Divide la siguiente clase en módulos más pequeños y cohesivos. Devuelve SOLO el código Python refactorizado, sin explicaciones.\n\n{class_code}"
                            try:
                                response = repair_agent.kickoff(prompt)
                                new_code = str(response.raw).strip() if hasattr(response, 'raw') else str(response).strip()
                                proposals.append({
                                    "title": f"Refactorizar clase '{node.name}' ({len(methods)} métodos)",
                                    "description": f"Clase con alta carga de métodos. Se sugiere dividirla.",
                                    "reason": "Principio de responsabilidad única",
                                    "suggested_code": new_code
                                })
                            except Exception:
                                pass  # Si falla, no añadimos la propuesta

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

    def _get_refactored_code(self, file_path: Path, func_name: str, func_code: str) -> str:
        """Usa el Repair Agent para generar una versión refactorizada de la función."""
        repair_agent = self._get_repair_agent()
        if not repair_agent:
            return self._extract_function_to_module(func_code, func_name, file_path.stem)

        prompt = f"""
Refactoriza la siguiente función Python '{func_name}' del archivo {file_path.name} para que sea más corta y legible.
Si es posible, extráela a una función auxiliar o simplifica su lógica.
Devuelve SOLO el código Python refactorizado, sin explicaciones.

{func_code}
"""
        try:
            response = repair_agent.kickoff(prompt)
            new_code = str(response.raw).strip() if hasattr(response, 'raw') else str(response).strip()
            if new_code:
                return new_code
        except Exception as e:
            print(f"[MetaAgent] Error al refactorizar con Repair Agent: {e}")

        # Fallback al método original
        return self._extract_function_to_module(func_code, func_name, file_path.stem)

    def _extract_function_to_module(self, func_code: str, func_name: str, module_name: str) -> str:
        """
        Genera el código de un nuevo módulo con la función extraída y las importaciones necesarias.
        Retorna el contenido del nuevo archivo .py.
        """
        lines = func_code.splitlines()
        new_module = f'"""\nMódulo auxiliar generado automáticamente para {func_name}\n"""\n\n'
        new_module += f'# Extraído de {module_name}.py\n'
        new_module += func_code
        return new_module

    def _analyze_from_memory(self) -> List[str]:
        ids = []
        issues = self.memory.validate()
        if issues:
            # Para imports rotos, pedimos ayuda al Repair Agent
            repair_agent = self._get_repair_agent()
            for issue in issues:
                suggested_code = ""
                if repair_agent:
                    prompt = f"Corrige el siguiente import roto en el archivo {issue.get('file', 'desconocido')}. Proporciona SOLO el código corregido.\n\nProblema: {issue.get('description', issue.get('target', ''))}"
                    try:
                        response = repair_agent.kickoff(prompt)
                        suggested_code = str(response.raw).strip() if hasattr(response, 'raw') else str(response).strip()
                    except Exception:
                        pass

                proposal_id = self.queue.add_proposal(
                    agent_name="MetaAgent",
                    title=f"Import roto en {issue.get('file', 'desconocido')}",
                    description=f"Problema detectado: {issue.get('target', '')}",
                    target_file=issue.get('file', 'workspace/backend'),
                    reason="Integridad del proyecto",
                    suggested_code=suggested_code
                )
                ids.append(proposal_id)
        return ids