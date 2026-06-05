import ast
import hashlib
import copy
import re
from pathlib import Path
from typing import List, Dict, Any
from core.tools.base_tool import BaseTool
from core.architecture_memory import ArchitectureMemory

# -------------------------------------------------------------------
#  HERRAMIENTAS BÁSICAS (todas sin tokens)
# -------------------------------------------------------------------

class EnsurePackagesTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="ensure_packages",
            description="Crea __init__.py faltantes en paquetes.",
            capabilities=["basic", "fix"]
        )

    def run(self, memory: ArchitectureMemory) -> List[Dict[str, Any]]:
        fixes = []
        for node in memory.nodes.values():
            if node.is_package:
                continue
            parent_dir = node.path.parent
            init_file = parent_dir / "__init__.py"
            if parent_dir.is_dir() and not init_file.exists():
                init_file.touch()
                fixes.append({
                    'rule': 'missing_init',
                    'file': str(init_file),
                    'action': 'created __init__.py'
                })
        return fixes


class FixProblematicRelativeImportsTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="fix_relative_imports",
            description="Convierte imports relativos profundos (>3 niveles) a absolutos.",
            capabilities=["basic", "fix"]
        )

    def run(self, memory: ArchitectureMemory) -> List[Dict[str, Any]]:
        fixes = []
        for pkg, node in memory.nodes.items():
            if not node.imports:
                continue
            try:
                with open(node.path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception:
                continue

            modified = False
            for imp in node.imports:
                if imp.import_type == 'relative' and '....' in imp.statement:
                    if imp.target_node:
                        for idx, line in enumerate(lines):
                            if imp.statement in line:
                                original = lines[idx].strip()
                                parts = original.split(' import ')
                                if len(parts) == 2:
                                    what = parts[1]
                                    new_line = f"from {imp.target_node.package} import {what}\n"
                                    lines[idx] = new_line
                                    modified = True
                                    fixes.append({
                                        'rule': 'deep_relative_import',
                                        'file': str(node.path),
                                        'original': original,
                                        'new': new_line.strip()
                                    })
            if modified:
                with open(node.path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
        return fixes


class LargeFileDetectorTool(BaseTool):
    def __init__(self, threshold: int = 300):
        super().__init__(
            name="large_file_detector",
            description=f"Detecta archivos con más de {threshold} líneas.",
            capabilities=["basic", "detection"]
        )
        self.threshold = threshold

    def run(self, memory: ArchitectureMemory) -> List[Dict[str, Any]]:
        findings = []
        for pkg, node in memory.nodes.items():
            try:
                num_lines = node.path.read_text(encoding='utf-8').count('\n')
                if num_lines > self.threshold:
                    findings.append({
                        'rule': 'large_file',
                        'file': str(node.path),
                        'lines': num_lines,
                        'suggestion': f'Consider splitting into smaller modules (> {self.threshold} lines)'
                    })
            except Exception:
                continue
        return findings


class OverloadedModuleDetectorTool(BaseTool):
    def __init__(self, threshold: int = 5):
        super().__init__(
            name="overloaded_module_detector",
            description="Detecta módulos con demasiadas clases o funciones.",
            capabilities=["basic", "detection"]
        )
        self.threshold = threshold

    def run(self, memory: ArchitectureMemory) -> List[Dict[str, Any]]:
        findings = []
        for pkg, node in memory.nodes.items():
            try:
                content = node.path.read_text(encoding='utf-8')
                classes = len(re.findall(r'^\s*class \w+', content, re.MULTILINE))
                functions = len(re.findall(r'^\s*def \w+', content, re.MULTILINE))
                total = classes + functions
                if total > self.threshold:
                    findings.append({
                        'rule': 'overloaded_module',
                        'file': str(node.path),
                        'classes': classes,
                        'functions': functions,
                        'total': total,
                        'suggestion': f'Module has {total} definitions (> {self.threshold}). Consider splitting.'
                    })
            except Exception:
                continue
        return findings


class UnusedImportDetectorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="unused_import_detector",
            description="Detecta imports que no se usan (análisis simple).",
            capabilities=["basic", "detection"]
        )

    def run(self, memory: ArchitectureMemory) -> List[Dict[str, Any]]:
        findings = []
        for pkg, node in memory.nodes.items():
            try:
                content = node.path.read_text(encoding='utf-8')
                for imp in node.imports:
                    if 'import' in imp.statement:
                        parts = imp.statement.split()
                        if parts[0] == 'import':
                            name = parts[1].split('.')[0]
                        elif parts[0] == 'from':
                            if 'import' in parts:
                                idx = parts.index('import')
                                name = parts[idx + 1].split(',')[0].strip()
                            else:
                                continue
                        else:
                            continue
                        code_without_imports = re.sub(r'^import .*$', '', content, flags=re.MULTILINE)
                        code_without_imports = re.sub(r'^from .* import .*$', '', code_without_imports, flags=re.MULTILINE)
                        if name not in code_without_imports:
                            findings.append({
                                'rule': 'unused_import',
                                'file': str(node.path),
                                'import': imp.statement,
                                'suggestion': f"'{name}' does not appear to be used"
                            })
            except Exception:
                continue
        return findings


# -------------------------------------------------------------------
#  HERRAMIENTAS EXTENDIDAS (se activan con extended=True)
# -------------------------------------------------------------------

class DuplicateCodeDetectorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="duplicate_code_detector",
            description="Detecta funciones/clases duplicadas usando fingerprinting AST.",
            capabilities=["extended", "detection"]
        )

    def run(self, memory: ArchitectureMemory) -> List[Dict[str, Any]]:
        duplicates_log = []
        fingerprints = {}

        for node in memory.nodes.values():
            try:
                source = node.path.read_text(encoding='utf-8')
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for stmt in ast.walk(tree):
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    normalized = self._normalize_node(stmt)
                    fp = hashlib.md5(normalized.encode()).hexdigest()
                    lineno = stmt.lineno
                    code = ast.get_source_segment(source, stmt)
                    if fp in fingerprints:
                        prev_file, prev_line, prev_code, count = fingerprints[fp]
                        if prev_file != str(node.path):
                            if count == 1:
                                duplicates_log.append({
                                    'rule': 'duplicate_code',
                                    'file1': prev_file,
                                    'line1': prev_line,
                                    'code': prev_code.strip()[:80],
                                    'suggestion': 'Código duplicado detectado'
                                })
                            duplicates_log.append({
                                'rule': 'duplicate_code',
                                'file2': str(node.path),
                                'line2': lineno,
                                'code': code.strip()[:80] if code else '',
                                'suggestion': 'Código duplicado detectado'
                            })
                            fingerprints[fp] = (prev_file, prev_line, prev_code, count + 1)
                    else:
                        fingerprints[fp] = (str(node.path), lineno, code, 1)
        return duplicates_log

    def _normalize_node(self, node) -> str:
        n = copy.deepcopy(node)
        for child in ast.walk(n):
            if isinstance(child, ast.Name):
                child.id = 'VAR'
            elif isinstance(child, ast.FunctionDef):
                child.name = 'FUNC'
            elif isinstance(child, ast.AsyncFunctionDef):
                child.name = 'AFUNC'
            elif isinstance(child, ast.ClassDef):
                child.name = 'CLASS'
            elif isinstance(child, ast.Constant):
                child.value = 'LIT'
            elif isinstance(child, ast.arg):
                child.arg = 'ARG'
            elif isinstance(child, ast.arguments):
                child.args = []
        return ast.dump(n, annotate_fields=False)