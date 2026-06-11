"""
Escáner dinámico de agentes, herramientas y módulos core.
No requiere modificar el código al añadir nuevos componentes.
"""
import ast
import json
from pathlib import Path
from typing import Dict, List, Optional

class ComponentScanner:
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path)

    def scan_agents(self) -> List[Dict]:
        """Busca archivos .py en agents/ y extrae nombre, rol y herramientas."""
        agents = []
        agents_dir = self.root / "agents"
        if not agents_dir.exists():
            return agents

        for py_file in agents_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            meta = self._parse_agent_file(py_file)
            if meta:
                agents.append(meta)
        return agents

    def _parse_agent_file(self, file_path: Path) -> Optional[Dict]:
        """Extrae role, goal y tools de un archivo de agente CrewAI mediante AST."""
        try:
            source = file_path.read_text(encoding='utf-8')
            tree = ast.parse(source)
        except:
            return None

        role = None
        goal = None
        tools = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == 'role' and isinstance(node.value, ast.Constant):
                            role = node.value.value
                        elif target.id == 'goal' and isinstance(node.value, ast.Constant):
                            goal = node.value.value
            if isinstance(node, ast.Call):
                if hasattr(node.func, 'id') and node.func.id == 'Agent':
                    for kw in node.keywords:
                        if kw.arg == 'role' and isinstance(kw.value, ast.Constant):
                            role = kw.value.value
                        elif kw.arg == 'goal' and isinstance(kw.value, ast.Constant):
                            goal = kw.value.value
                        elif kw.arg == 'tools' and isinstance(kw.value, ast.List):
                            tools = [self._get_tool_name(elt) for elt in kw.value.elts]

        if not role:
            return None

        return {
            "name": file_path.stem.replace("_agent", "").replace("_", " ").title(),
            "role": role,
            "goal": goal or "",
            "tools": tools,
            "emoji": self._guess_emoji(role),
            "status": "idle",
            "description": goal or role
        }

    def _get_tool_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Call) and hasattr(node.func, 'id'):
            return node.func.id
        return "desconocida"

    def _guess_emoji(self, role: str) -> str:
        r = role.lower()
        if "director" in r or "arquitecto" in r: return "🧠"
        if "backend" in r or "code" in r: return "💻"
        if "frontend" in r or "diseñador" in r: return "🎨"
        if "qa" in r or "auditor" in r: return "🔍"
        if "repair" in r or "debug" in r: return "🔧"
        if "depend" in r: return "📦"
        return "🤖"

    def scan_tools(self) -> List[Dict]:
        """Busca herramientas en tools/ y extrae nombres y descripciones."""
        tools = []
        tools_dir = self.root / "tools"
        if not tools_dir.exists():
            return tools

        for py_file in tools_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                source = py_file.read_text(encoding='utf-8')
                tree = ast.parse(source)
            except:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Solo funciones con docstring y decorador @tool
                    if node.decorator_list and len(node.body) > 0:
                        doc = ast.get_docstring(node)
                        if doc:
                            tools.append({
                                "name": node.name,
                                "description": doc.strip()
                            })
        return tools

    def scan_core_modules(self) -> List[Dict]:
        """Busca módulos en core/ y extrae descripciones de docstrings."""
        modules = []
        core_dir = self.root / "core"
        if not core_dir.exists():
            return modules

        for py_file in core_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                source = py_file.read_text(encoding='utf-8')
                tree = ast.parse(source)
                doc = ast.get_docstring(tree)
                modules.append({
                    "name": py_file.stem,
                    "description": doc.strip().split('\n')[0] if doc else "Módulo del sistema"
                })
            except:
                continue
        return modules

    def load_teams(self) -> List[Dict]:
        """Carga la configuración de equipos desde teams.json o usa el equipo por defecto."""
        teams_path = self.root / "teams.json"
        if teams_path.exists():
            try:
                return json.loads(teams_path.read_text(encoding='utf-8'))
            except:
                pass

        # Equipo por defecto con todos los agentes
        agents = self.scan_agents()
        return [
            {
                "name": "Equipo General",
                "description": "Todos los agentes disponibles en el ecosistema.",
                "agents": [a["name"] for a in agents]
            }
        ]

    def get_full_data(self) -> Dict:
        """Devuelve la estructura completa para el endpoint /api/agents."""
        agents = self.scan_agents()
        tools = self.scan_tools()
        core_modules = self.scan_core_modules()
        teams_config = self.load_teams()

        # Construir equipos con los metadatos completos de los agentes
        teams = []
        agent_map = {a["name"]: a for a in agents}
        for team_cfg in teams_config:
            members = []
            for name in team_cfg.get("agents", []):
                if name in agent_map:
                    members.append(agent_map[name])
                else:
                    # Agente definido en teams.json pero no encontrado en agents/
                    members.append({
                        "name": name,
                        "role": "Desconocido",
                        "emoji": "🤖",
                        "status": "idle",
                        "tools": [],
                        "description": "Agente no encontrado en el sistema"
                    })
            teams.append({
                "name": team_cfg.get("name", "Sin nombre"),
                "description": team_cfg.get("description", ""),
                "agents": members
            })

        return {
            "teams": teams,
            "tools": tools,
            "core_modules": core_modules
        }