"""
Herramientas de limpieza y análisis de código para los agentes.
Ejecuta black, isort y bandit sobre archivos Python generados.
"""
import subprocess
import sys
from pathlib import Path
from typing import Optional

def format_with_black(file_path: str) -> str:
    """Formatea un archivo Python con Black."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--quiet", file_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return f"✅ {file_path} formateado con Black."
        else:
            return f"⚠️ Black encontró errores en {file_path}: {result.stderr[:200]}"
    except FileNotFoundError:
        return "❌ Black no está instalado. Ejecutá: pip install black"
    except Exception as e:
        return f"❌ Error al formatear {file_path}: {str(e)}"

def sort_imports(file_path: str) -> str:
    """Ordena los imports de un archivo Python con isort."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", "--quiet", file_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return f"✅ Imports ordenados en {file_path}."
        else:
            return f"⚠️ isort encontró errores en {file_path}: {result.stderr[:200]}"
    except FileNotFoundError:
        return "❌ isort no está instalado. Ejecutá: pip install isort"
    except Exception as e:
        return f"❌ Error al ordenar imports en {file_path}: {str(e)}"

def check_security(file_path: str) -> str:
    """Analiza un archivo Python con Bandit en busca de vulnerabilidades."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", "-q", file_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return f"✅ {file_path} sin problemas de seguridad."
        else:
            return f"⚠️ Bandit encontró problemas en {file_path}:\n{result.stdout[:300]}"
    except FileNotFoundError:
        return "❌ Bandit no está instalado. Ejecutá: pip install bandit"
    except Exception as e:
        return f"❌ Error al analizar {file_path}: {str(e)}"

def clean_backend_code(backend_path: Optional[str] = None) -> str:
    """Aplica black, isort y bandit a todos los archivos .py en backend/."""
    if backend_path is None:
        backend_path = "backend"
    
    backend_dir = Path(backend_path)
    if not backend_dir.exists():
        return f"❌ Carpeta '{backend_path}' no encontrada."

    results = []
    for py_file in backend_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        file_str = str(py_file)
        results.append(format_with_black(file_str))
        results.append(sort_imports(file_str))
        results.append(check_security(file_str))
    
    return "\n".join(results) if results else "No se encontraron archivos Python para limpiar."