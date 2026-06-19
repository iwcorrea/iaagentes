"""
Validador de sintaxis temprana.
Comprueba archivos .py y .jsx sin ejecutarlos, sin gastar tokens.
Si encuentra errores, los reporta para que el Repair Agent los corrija.
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class SyntaxValidator:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)

    def validate_backend(self) -> List[str]:
        """Valida todos los archivos .py del backend. Retorna lista de errores."""
        errors = []
        backend_path = self.workspace_path / "backend"
        if not backend_path.exists():
            return errors

        for py_file in backend_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                source = py_file.read_text(encoding='utf-8')
                compile(source, str(py_file), 'exec')
            except SyntaxError as e:
                errors.append(f"{py_file.relative_to(self.workspace_path)}: {e}")
        return errors

    def validate_frontend(self) -> List[str]:
        """Valida todos los archivos .jsx del frontend usando Node.js (si está disponible)."""
        errors = []
        frontend_path = self.workspace_path / "frontend"
        if not frontend_path.exists():
            return errors

        for jsx_file in frontend_path.rglob("*.jsx"):
            try:
                # Usamos Node.js para verificar sintaxis básica
                result = subprocess.run(
                    ["node", "--check", str(jsx_file)],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode != 0:
                    errors.append(f"{jsx_file.relative_to(self.workspace_path)}: {result.stderr.strip()}")
            except FileNotFoundError:
                errors.append("Node.js no está instalado. No se puede validar sintaxis JSX.")
                break
            except subprocess.TimeoutExpired:
                errors.append(f"Timeout validando {jsx_file.name}")
            except Exception as e:
                errors.append(f"Error validando {jsx_file.name}: {str(e)}")
        return errors

    def validate_all(self) -> List[str]:
        """Valida todo el proyecto y retorna todos los errores encontrados."""
        errors = []
        errors.extend(self.validate_backend())
        errors.extend(self.validate_frontend())
        return errors