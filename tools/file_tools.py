import os
from crewai.tools import tool

@tool("Read File Content")
def read_file(file_path: str) -> str:
    """
    Lee el contenido de un archivo específico del proyecto.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: El archivo '{file_path}' no existe."
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error leyendo el archivo: {str(e)}"

@tool("Write File Content")
def write_file(data: str, file_path: str) -> str:
    """
    Crea o sobrescribe un archivo con el contenido de texto proporcionado.
    """
    try:
        # Asegurar que las carpetas contenedoras existan
        dir_name = os.path.dirname(file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data)
        return f"Éxito: Archivo guardado correctamente en '{file_path}'"
    except Exception as e:
        return f"Error escribiendo el archivo: {str(e)}"