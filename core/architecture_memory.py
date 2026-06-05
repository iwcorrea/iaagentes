import ast
import networkx as nx
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
import importlib.util
import re

# -----------------------------------------------
# DATACLASSES DEL GRAFO
# -----------------------------------------------

@dataclass
class ImportEdge:
    source_node: Optional['ModuleNode'] = None
    target_node: Optional['ModuleNode'] = None
    import_type: str = ''          # 'absolute', 'relative', 'external', 'broken'
    statement: str = ''            # la línea original
    line_no: int = 0

@dataclass
class ModuleNode:
    path: Path
    package: str                   # nombre completo del paquete (ej: 'backend.api.models')
    is_package: bool = False       # True si el archivo es __init__.py
    imports: List[ImportEdge] = field(default_factory=list)


# -----------------------------------------------
# ARCHITECTURE MEMORY
# -----------------------------------------------

class ArchitectureMemory:
    """
    Cerebro arquitectónico. Construye el Project Graph, valida dependencias,
    detecta ciclos, repara imports rotos y diagnostica errores en runtime.
    """

    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, ModuleNode] = {}   # clave = dotted package path

    # ------------------------------------------------------------
    # ESCANEO DEL PROYECTO
    # ------------------------------------------------------------
    def scan_project(self):
        """Descubre todos los módulos y paquetes del proyecto bajo self.root."""
        self.graph.clear()
        self.nodes.clear()

        # 1. Registrar todos los archivos .py
        for py_file in self.root.rglob('*.py'):
            rel = py_file.relative_to(self.root)
            if rel.name == '__init__.py':
                parts = rel.parent.parts
                package = '.'.join(parts) if parts else ''
                node = ModuleNode(path=py_file, package=package, is_package=True)
            else:
                module_name = rel.stem
                parts = rel.parent.parts
                package = '.'.join(parts + (module_name,)) if parts else module_name
                node = ModuleNode(path=py_file, package=package, is_package=False)

            self.nodes[node.package] = node
            self.graph.add_node(node.package, data=node)

        # 2. Analizar imports de cada módulo
        for pkg, node in self.nodes.items():
            self._analyze_imports(node)

    def _analyze_imports(self, node: ModuleNode):
        """Parsea el AST de un módulo para extraer sus imports."""
        node.imports.clear()
        try:
            with open(node.path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            return

        for stmt in ast.walk(tree):
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    self._process_absolute_import(node, alias.name, stmt.lineno)
            elif isinstance(stmt, ast.ImportFrom):
                module = stmt.module or ''
                level = stmt.level
                self._process_import_from(node, module, level, stmt.lineno)

    def _process_absolute_import(self, node: ModuleNode, full_name: str, line: int):
        edge = ImportEdge(
            source_node=node,
            import_type='absolute',
            statement=f'import {full_name}',
            line_no=line
        )
        if full_name in self.nodes:
            edge.target_node = self.nodes[full_name]
            edge.import_type = 'absolute'
        else:
            top_module = full_name.split('.')[0]
            spec = importlib.util.find_spec(top_module)
            if spec is not None:
                edge.import_type = 'external'
            else:
                edge.import_type = 'broken'
        node.imports.append(edge)
        if edge.target_node:
            self.graph.add_edge(node.package, full_name, edge=edge)

    def _process_import_from(self, node: ModuleNode, module: str, level: int, line: int):
        if level > 0:
            target_pkg = self._resolve_relative(node.package, module, level)
            stmt = f'from {"."*level}{module} import ...'
        else:
            target_pkg = module
            stmt = f'from {module} import ...'

        edge = ImportEdge(
            source_node=node,
            statement=stmt,
            line_no=line
        )

        if target_pkg and target_pkg in self.nodes:
            edge.target_node = self.nodes[target_pkg]
            edge.import_type = 'relative' if level > 0 else 'absolute'
        else:
            if level == 0:
                top = module.split('.')[0] if module else ''
                if top and importlib.util.find_spec(top):
                    edge.import_type = 'external'
                else:
                    edge.import_type = 'broken'
            else:
                edge.import_type = 'broken'

        node.imports.append(edge)
        if edge.target_node:
            self.graph.add_edge(node.package, target_pkg, edge=edge)

    def _resolve_relative(self, source_pkg: str, module: str, level: int) -> Optional[str]:
        if not source_pkg:
            return None
        parts = source_pkg.split('.')
        if level > len(parts):
            return None
        base = '.'.join(parts[:-level]) if level < len(parts) else ''
        if module:
            return f"{base}.{module}" if base else module
        else:
            return base

    # ------------------------------------------------------------
    # VALIDACIÓN
    # ------------------------------------------------------------
    def validate(self) -> List[Dict[str, Any]]:
        """Busca y reporta problemas en las importaciones detectadas."""
        issues = []
        for pkg, node in self.nodes.items():
            for imp in node.imports:
                if imp.import_type == 'broken':
                    issues.append({
                        'type': 'broken_import',
                        'source': pkg,
                        'target': imp.statement,
                        'line': imp.line_no,
                        'severity': 'error',
                        'file': str(node.path)
                    })
        return issues

    # ------------------------------------------------------------
    # REPARACIÓN GLOBAL (placeholder)
    # ------------------------------------------------------------
    def fix_imports_globally(self) -> List[Dict[str, Any]]:
        """
        Repara imports rotos detectados.
        (Implementación real pendiente)
        """
        # Por ahora devolvemos lista vacía para no romper el pipeline.
        return []

    # ------------------------------------------------------------
    # EXPORTACIÓN DEL GRAFO
    # ------------------------------------------------------------
    def export_graphviz(self) -> str:
        """
        Exporta el grafo arquitectónico a formato DOT (Graphviz).
        Incluye nodos externos/rotos como nodos artificiales para visualización completa.
        """
        lines = ['digraph ArchitectureGraph {']
        lines.append('  rankdir=TB;')
        lines.append('  node [shape=box, style=filled, fontname="Arial"];')
        lines.append('  edge [fontname="Arial", fontsize=10];')
        lines.append('')

        # Colores por tipo de archivo (palabras clave)
        color_map = {
            '__init__': '#E8F5E9',   # verde claro (paquetes)
            'router': '#E3F2FD',     # azul claro
            'model': '#FFF3E0',      # naranja claro
            'service': '#FCE4EC',    # rosa claro
            'main': '#FFEBEE',       # rojo claro
        }

        # Definir nodos existentes
        for pkg, node in self.nodes.items():
            color = '#F5F5F5'  # gris claro por defecto
            for keyword, c in color_map.items():
                if keyword in pkg.lower():
                    color = c
                    break
            
            shape = 'folder' if node.is_package else 'box'
            label = pkg if node.is_package else pkg.split('.')[-1]
            lines.append(f'  "{pkg}" [label="{label}", shape={shape}, fillcolor="{color}"];')

        lines.append('')

        # Recolectar imports externos/rotos para crear nodos artificiales
        external_nodes = set()
        broken_nodes = set()

        for pkg, node in self.nodes.items():
            for imp in node.imports:
                if imp.import_type == 'external':
                    # Nombre del módulo externo (top-level)
                    mod_name = imp.statement.split()[1].split('.')[0] if imp.statement.startswith('import ') else imp.statement.split()[1].split('.')[0] if ' import ' in imp.statement else 'unknown'
                    external_nodes.add(mod_name)
                elif imp.import_type == 'broken':
                    # Representar la sentencia rota como nodo
                    broken_nodes.add(imp.statement)

        # Agregar nodos artificiales para externos
        for node_name in external_nodes:
            if node_name not in self.nodes:
                lines.append(f'  "{node_name}" [label="{node_name}\\n(ext)", shape=oval, fillcolor="#E3F2FD", fontsize=9];')

        # Agregar nodos para rotos
        for stmt in broken_nodes:
            broken_id = stmt.replace(' ', '_').replace('.', '_')[:30]
            if broken_id not in self.nodes:
                lines.append(f'  "{broken_id}" [label="{stmt}", shape=oval, fillcolor="#FFCDD2", fontsize=9];')

        # Definir aristas
        for pkg, node in self.nodes.items():
            for imp in node.imports:
                if imp.target_node:
                    # Interno
                    target = imp.target_node.package
                    style = 'dashed' if imp.import_type == 'relative' else 'solid'
                    color = '#4CAF50' if imp.import_type == 'relative' else '#1E88E5'
                    lines.append(f'  "{pkg}" -> "{target}" [style={style}, color="{color}"];')
                elif imp.import_type == 'external':
                    mod_name = imp.statement.split()[1].split('.')[0] if imp.statement.startswith('import ') else imp.statement.split()[1].split('.')[0] if ' import ' in imp.statement else 'unknown'
                    lines.append(f'  "{pkg}" -> "{mod_name}" [style=dotted, color="#1976D2", label="ext"];')
                elif imp.import_type == 'broken':
                    broken_id = imp.statement.replace(' ', '_').replace('.', '_')[:30]
                    lines.append(f'  "{pkg}" -> "{broken_id}" [style=bold, color="#D32F2F", label="roto"];')

        # Leyenda compacta
        lines.append('')
        lines.append('  subgraph cluster_legend {')
        lines.append('    label="Leyenda";')
        lines.append('    style=dashed;')
        lines.append('    bgcolor="#FAFAFA";')
        lines.append('    node [shape=box, style=filled, fontsize=10];')
        lines.append('    leg_package [label="Paquete", fillcolor="#E8F5E9"];')
        lines.append('    leg_module [label="Módulo", fillcolor="#F5F5F5"];')
        lines.append('    leg_external [label="Externo", shape=oval, fillcolor="#E3F2FD"];')
        lines.append('    leg_broken [label="Roto", shape=oval, fillcolor="#FFCDD2"];')
        lines.append('')
        lines.append('    edge [fontsize=8];')
        lines.append('    leg_package -> leg_module [style=solid, color="#1E88E5", label="absoluto"];')
        lines.append('    leg_package -> leg_module [style=dashed, color="#4CAF50", label="relativo"];')
        lines.append('    leg_external -> leg_module [style=dotted, color="#1976D2", label="externo"];')
        lines.append('    leg_broken -> leg_module [style=bold, color="#D32F2F", label="roto"];')
        lines.append('  }')

        lines.append('}')
        return '\n'.join(lines)