import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

# =========================================================
#  EXTRACCIÓN DE ARCHIVOS (PARSER ROBUSTO CON REINTENTOS)
# =========================================================
def execute_plan(raw_output: str, workspace_base: Optional[Path] = None) -> str:
    if workspace_base is None:
        workspace_base = Path("workspace")
    workspace_base.mkdir(parents=True, exist_ok=True)

    lines = raw_output.splitlines()
    files_created = []
    pending_file = None
    pending_code = []

    file_pattern = re.compile(r'^([\w\-./\\]+\.(?:py|jsx?|tsx?|css|html|yaml|json|txt))\s*(.*)')

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        if ":::" in line_str:
            if pending_file:
                full_path = workspace_base / pending_file
                full_path.parent.mkdir(parents=True, exist_ok=True)
                content = '\n'.join(pending_code).strip()
                if content:
                    for attempt in range(3):
                        try:
                            full_path.write_text(content, encoding='utf-8')
                            break
                        except PermissionError:
                            if attempt < 2:
                                print(f"[EXECUTOR] Permiso denegado para {full_path}, reintentando en 2s...")
                                time.sleep(2)
                            else:
                                raise
                    files_created.append(str(full_path.relative_to(workspace_base)))
            parts = line_str.split(":::", 1)
            clean_path = parts[0].strip()
            for prefix in ["backend/", "workspace/", "frontend/"]:
                if clean_path.startswith(prefix):
                    clean_path = clean_path[len(prefix):]
            pending_file = clean_path
            pending_code = [parts[1].strip()] if len(parts) > 1 and parts[1].strip() else []
        else:
            match = file_pattern.match(line_str)
            if match:
                file_name = match.group(1)
                rest = match.group(2).strip()
                if not pending_file or file_name != pending_file:
                    if pending_file:
                        full_path = workspace_base / pending_file
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        content = '\n'.join(pending_code).strip()
                        if content:
                            for attempt in range(3):
                                try:
                                    full_path.write_text(content, encoding='utf-8')
                                    break
                                except PermissionError:
                                    if attempt < 2:
                                        print(f"[EXECUTOR] Permiso denegado para {full_path}, reintentando en 2s...")
                                        time.sleep(2)
                                    else:
                                        raise
                            files_created.append(str(full_path.relative_to(workspace_base)))
                    clean_path = file_name
                    for prefix in ["backend/", "workspace/", "frontend/"]:
                        if clean_path.startswith(prefix):
                            clean_path = clean_path[len(prefix):]
                    pending_file = clean_path
                    pending_code = [rest] if rest else []
                    continue
            if pending_file is not None:
                pending_code.append(line)

    if pending_file and pending_code:
        full_path = workspace_base / pending_file
        full_path.parent.mkdir(parents=True, exist_ok=True)
        content = '\n'.join(pending_code).strip()
        if content:
            for attempt in range(3):
                try:
                    full_path.write_text(content, encoding='utf-8')
                    break
                except PermissionError:
                    if attempt < 2:
                        print(f"[EXECUTOR] Permiso denegado para {full_path}, reintentando en 2s...")
                        time.sleep(2)
                    else:
                        raise
            files_created.append(str(full_path.relative_to(workspace_base)))

    if not files_created:
        fallback_path = workspace_base / "main.py"
        fallback_path.write_text(raw_output, encoding='utf-8')
        files_created.append("main.py (contenido crudo)")

    summary = f"Archivos creados en {workspace_base}:\n" + '\n'.join(f"  - {f}" for f in files_created)
    return summary


# =========================================================
#  EJECUCIÓN INTELIGENTE DEL PROYECTO
# =========================================================
class ProjectExecutor:
    def __init__(self, project_path: str, memory=None):
        self.project_path = Path(project_path).resolve()
        self.memory = memory

    def execute_project(self, entry_module: Optional[str] = None) -> Dict[str, Any]:
        main_file = self._find_main_file(entry_module)
        if not main_file:
            return {
                'success': False,
                'stderr': 'No se encontró un punto de entrada (main.py o app).',
                'stdout': '',
                'traceback': ''
            }

        is_fastapi = self._is_fastapi_app(main_file)
        execution_type = 'uvicorn' if is_fastapi else 'python'
        result = self._run(main_file, execution_type)
        result['execution_type'] = execution_type
        return result

    def _find_main_file(self, entry_module: Optional[str]) -> Optional[Path]:
        if entry_module:
            module_path = self.project_path / f"{entry_module}.py"
            if module_path.exists():
                return module_path
            pkg_main = self.project_path / entry_module / "__main__.py"
            if pkg_main.exists():
                return pkg_main
            return None

        for candidate in ['main.py', 'app.py']:
            path = self.project_path / candidate
            if path.exists():
                return path

        for sub in ['backend', 'app', 'src']:
            for candidate in ['main.py', 'app.py']:
                path = self.project_path / sub / candidate
                if path.exists():
                    return path
        return None

    def _is_fastapi_app(self, main_file: Path) -> bool:
        try:
            content = main_file.read_text(encoding='utf-8')
            if 'FastAPI' in content:
                return True
        except Exception:
            pass
        return False

    def _run(self, main_file: Path, execution_type: str) -> Dict[str, Any]:
        workspace_root = self.project_path
        if execution_type == 'uvicorn':
            try:
                rel = main_file.relative_to(workspace_root)
                module_path = str(rel.with_suffix('')).replace('/', '.').replace('\\', '.')
            except ValueError:
                module_path = "main"
            app_variable = self._find_app_variable(main_file)
            target = f"{module_path}:{app_variable}"
            py_path = str(workspace_root)
            cmd = [sys.executable, '-m', 'uvicorn', target, '--host', '0.0.0.0', '--port', '8001']
            cwd = workspace_root
        else:
            cmd = [sys.executable, str(main_file)]
            py_path = str(workspace_root)
            cwd = main_file.parent

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=15,
                env={**os.environ, 'PYTHONPATH': py_path}
            )
            stdout = proc.stdout
            stderr = proc.stderr
            success = proc.returncode == 0
        except subprocess.TimeoutExpired:
            if execution_type == 'uvicorn':
                stdout = "Uvicorn iniciado correctamente (timeout esperado)."
                stderr = ""
                success = True
            else:
                stdout = ""
                stderr = "Timeout: la ejecución tardó demasiado."
                success = False
        except Exception as e:
            stdout = ""
            stderr = f"Error al ejecutar: {str(e)}"
            success = False

        return {
            'success': success,
            'stdout': stdout,
            'stderr': stderr,
            'traceback': stderr if not success else ''
        }

    def _find_app_variable(self, main_file: Path) -> str:
        try:
            content = main_file.read_text()
            match = re.search(r'(\w+)\s*=\s*FastAPI\(', content)
            if match:
                return match.group(1)
        except Exception:
            pass
        return 'app'