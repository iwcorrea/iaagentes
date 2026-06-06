from crewai.tools import tool

@tool("Read File")
def read_file(path: str) -> str:
    """
    Lee el contenido de un archivo específico del proyecto.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: El archivo '{path}' no existe."
    except Exception as e:
        return f"Error al leer '{path}': {str(e)}"

@tool("Write File")
def write_file(args: str) -> str:
    """
    Escribe contenido en un archivo. Formato: 'ruta:::contenido'.
    """
    try:
        if ":::" in args:
            path, content = args.split(":::", 1)
        else:
            parts = args.split(" ", 1)
            path = parts[0]
            content = parts[1] if len(parts) > 1 else ""
        with open(path.strip(), 'w', encoding='utf-8') as f:
            f.write(content.strip())
        return f"Archivo guardado correctamente en '{path.strip()}'"
    except Exception as e:
        return f"Error al escribir archivo: {str(e)}"

@tool("Run Terminal")
def run_terminal(command: str) -> str:
    """
    Ejecuta un comando en la terminal y devuelve la salida.
    """
    import subprocess
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        return output if output else "Comando ejecutado sin salida."
    except subprocess.TimeoutExpired:
        return "Error: El comando excedió el tiempo de espera (30s)."
    except Exception as e:
        return f"Error al ejecutar comando: {str(e)}"