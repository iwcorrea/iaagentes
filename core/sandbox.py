# core/sandbox.py
"""
Entorno aislado para probar cambios de código antes de aplicarlos.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple


def test_improvement(target_file: str, new_code: str, test_command: Optional[str] = None) -> Tuple[bool, str]:
    """
    Valida un cambio de código en un directorio temporal.
    - Crea el nuevo archivo con el código propuesto.
    - Ejecuta verificación de sintaxis (para .py).
    - Si se proporciona test_command, lo ejecuta en el entorno temporal.
    - No modifica el archivo original.
    
    Retorna (éxito, mensaje).
    """
    target = Path(target_file)
    if not target.exists():
        return False, f"Archivo objetivo no encontrado: {target_file}"

    # Crear directorio temporal espejo
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_target = Path(tmpdir) / target.name

        # Copiar archivo original al temporal
        shutil.copy2(target, tmp_target)

        # Escribir el nuevo código en el temporal
        try:
            tmp_target.write_text(new_code, encoding='utf-8')
        except Exception as e:
            return False, f"Error escribiendo código temporal: {e}"

        # Verificación básica: compilar si es Python
        if target.suffix == '.py':
            try:
                compile(new_code, str(target_file), 'exec')
            except SyntaxError as e:
                return False, f"Error de sintaxis: {e}"

        # Ejecutar comando de prueba opcional
        if test_command:
            try:
                result = subprocess.run(
                    test_command, shell=True, capture_output=True, text=True,
                    timeout=30, cwd=tmpdir
                )
                if result.returncode != 0:
                    return False, f"Test falló (código {result.returncode}): {result.stderr[:200]}"
            except subprocess.TimeoutExpired:
                return False, "Timeout en el test de validación"
            except Exception as e:
                return False, f"Error ejecutando test: {e}"

    return True, "Validación exitosa"


def apply_improvement_safe(target_file: str, new_code: str, test_command: Optional[str] = None) -> Tuple[bool, str]:
    """
    Aplica un cambio de código con backup y validación sandbox.
    1. Crea backup (.bak).
    2. Prueba en sandbox.
    3. Si es válido, aplica. Si no, restaura backup.
    
    Retorna (éxito, mensaje).
    """
    target = Path(target_file)
    backup_path = target.with_suffix(target.suffix + '.bak')

    # Backup
    try:
        shutil.copy2(target, backup_path)
    except Exception as e:
        return False, f"Error creando backup: {e}"

    # Validar
    success, msg = test_improvement(str(target), new_code, test_command)
    if not success:
        return False, f"Validación fallida ({msg}). Backup en {backup_path}"

    # Aplicar
    try:
        target.write_text(new_code, encoding='utf-8')
    except Exception as e:
        shutil.copy2(backup_path, target)
        return False, f"Error escribiendo archivo ({e}). Restaurado backup."

    return True, f"Cambio aplicado. Backup: {backup_path}"