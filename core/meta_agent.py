"""
MetaAgent - Analiza el sistema y propone mejoras con código sugerido real.
Utiliza análisis estático + Repair Agent para generar correcciones completas.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any
from core.architecture_memory import ArchitectureMemory
from core.improvement_queue import ImprovementQueue
from agents.repair_agent import repair_agent


class MetaAgent:
    """
    Agente que analiza el sistema y propone mejoras con código sugerido.
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
            # Funciones largas -> pedir al Repair Agent que refactorice
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, 'end_lineno', node.lineno)
                length = end_line - node.lineno
                if length > 30:
                    func_code = ast.get_source_segment(source, node)
                    if func_code:
                        new_code = self._get_repair_suggestion(
                            file_path=file_path,
                            issue=f"La función '{node.name}' tiene {length} líneas. Refactorízala en un módulo auxiliar manteniendo toda la funcionalidad.",
                            original_code=source
                        )
                        if new_code:
                            proposals.append({
                                "title": f"Refactorizar función '{node.name}' ({length} líneas)",
                                "description": f"La función es demasiado larga. Se sugiere extraerla a un módulo auxiliar.",
                                "reason": "Reduce complejidad y mejora legibilidad",
                                "suggested_code": new_code
                            })

            # Clases con muchos métodos -> sugerir división (sin código automático por ahora)
            if isinstance(node, ast.ClassDef):
                methods = [n for n in ast.iter_child_nodes(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                if len(methods) > 10:
                    proposals.append({
                        "title": f"Clase '{node.name}' con {len(methods)} métodos",
                        "description": f"La clase tiene {len(methods)} métodos. Evalúa dividirla en clases más pequeñas.",
                        "reason": "Principio de responsabilidad única",
                        "suggested_code": ""
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

    def _analyze_from_memory(self) -> List[str]:
        """
        Analiza los imports rotos detectados por ArchitectureMemory y genera
        propuestas con código sugerido completo (archivo entero corregido).
        """
        ids = []
        issues = self.memory.validate()
        for issue in issues:
            if issue['type'] == 'broken_import':
                target_file = Path(issue['file'])
                if target_file.exists():
                    original_code = target_file.read_text(encoding='utf-8')
                    new_code = self._get_repair_suggestion(
                        file_path=target_file,
                        issue=f"Corrige el import roto: {issue['target']}. El archivo completo debe mantenerse intacto; solo corrige esa línea de import.",
                        original_code=original_code
                    )
                    if new_code:
                        proposal_id = self.queue.add_proposal(
                            agent_name="MetaAgent",
                            title=f"Reparar import roto en {issue['file']}",
                            description=f"Se detectó un import roto: {issue['target']}. El código sugerido reemplazará todo el archivo con la corrección.",
                            target_file=str(target_file.relative_to(Path.cwd())),
                            reason="Integridad del proyecto",
                            suggested_code=new_code
                        )
                        ids.append(proposal_id)
        return ids

    def _get_repair_suggestion(self, file_path: Path, issue: str, original_code: str) -> str:
        """
        Llama al Repair Agent para obtener una versión corregida del archivo completo.
        """
        try:
            prompt = f"""
Tienes que corregir el siguiente archivo. El problema es:
{issue}

REGLAS OBLIGATORIAS:
- Devuelve el archivo COMPLETO con la corrección aplicada.
- NO devuelvas solo la línea corregida.
- NO añadas explicaciones, comentarios ni markdown.
- El código debe ser idéntico al original, excepto la línea(s) corregida(s).

ARCHIVO ORIGINAL:
{original_code}
"""
            response = repair_agent.kickoff(prompt)
            if hasattr(response, 'raw'):
                return str(response.raw).strip()
            return str(response).strip()
        except Exception as e:
            print(f"[MetaAgent] Error llamando al Repair Agent: {e}")
            return ""