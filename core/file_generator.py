"""
Generador de archivos individuales usando el backend agent.
Se usa cuando la API detecta intención 'create_file'.
"""

import re
from pathlib import Path
from agents.backend_agent import backend_agent


def generate_file(prompt: str, project_path: Path = Path("workspace")) -> str:
    """
    Genera un archivo según el prompt y lo guarda dentro de project_path.
    """
    try:
        # Detectar ruta dentro del proyecto
        path_match = re.search(r"([a-zA-Z0-9_\-\/\.]+\.[a-zA-Z]+)", prompt)
        if path_match:
            file_rel = path_match.group(1).lstrip("/")
        else:
            file_rel = "backend/main.py"

        # Ruta absoluta dentro del proyecto
        full_file_path = project_path / file_rel

        response = backend_agent.kickoff(
            f"""
TASK:

{prompt}

RULES:
- Generate ONLY code
- No explanations
- No markdown
- No talking
- Keep compatibility with existing architecture
- Output ONLY raw code, nothing else
"""
        )

        if response is None:
            return "LLM ERROR: The model returned None."

        # Extraer código de la respuesta
        if hasattr(response, 'raw'):
            code = str(response.raw).strip()
        else:
            code = str(response).strip()

        if not code:
            return "LLM ERROR: Empty code response."

        # Limpiar markdown
        if "```" in code:
            match = re.search(r"```(?:python)?\s*([\s\S]*?)```", code)
            if match:
                code = match.group(1).strip()
            else:
                code = code.replace("```python", "").replace("```", "").strip()

        # Escribir archivo
        full_file_path.parent.mkdir(parents=True, exist_ok=True)
        full_file_path.write_text(code, encoding="utf-8")

        return f"FILE GENERATED:\n\n{file_rel}\n\n====================\n\nArchivo guardado correctamente en '{full_file_path}'"

    except Exception as e:
        return f"FILE GENERATION ERROR:\n\n{str(e)}"