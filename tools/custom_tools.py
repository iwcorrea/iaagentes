import os
from crewai.tools import tool

@tool("Read File")
def read_file(path: str) -> str:
    """
    Lee el contenido de un archivo específico del proyecto.
    """
    try:
        if not os.path.exists(path):
            return f"Error: El archivo '{path}' no existe."
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"ERROR leyendo archivo: {str(e)}"

@tool("Write File")
def write_file(data: str) -> str:
    """
    Escribe archivos reales. El parámetro 'data' debe tener el formato 'ruta:::contenido'.
    """
    try:
        if ":::" not in data:
            return "Error: Formato incorrecto. Usa 'ruta:::contenido'."
        file_path, content = data.split(":::", 1)
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Archivo guardado correctamente en '{file_path}'"
    except Exception as e:
        return f"Error escribiendo archivo: {str(e)}"

@tool("Run Terminal")
def run_terminal(command: str) -> str:
    """
    Ejecuta un comando en la terminal y devuelve la salida.
    """
    import subprocess
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error ejecutando comando: {str(e)}"