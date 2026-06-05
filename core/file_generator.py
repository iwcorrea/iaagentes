import re
from pathlib import Path
from agents.backend_agent import backend_agent
from tools.custom_tools import write_file
from core.project_context import get_project_context

# ==========================================
# GENERATE FILE (ADAPTATIVO)
# ==========================================
def generate_file(prompt: str, project_path: Path = Path("workspace")) -> str:
    """
    Genera un archivo según el prompt y lo guarda dentro de project_path.
    """
    try:
        # ======================================
        # DETECT FILE PATH (Flexible)
        # ======================================
        path_match = re.search(
            r"([a-zA-Z0-9_\-\/\.]+\.[a-zA-Z]+)",
            prompt
        )
        if path_match:
            file_rel = path_match.group(1).lstrip("/")
        else:
            # FALLBACK INTELIGENTE: Si el usuario no da una ruta, asumimos main.py
            print("[FILE GENERATOR] No se detectó ruta explícita en el prompt. Usando main.py por defecto.")
            file_rel = "backend/main.py"

        # Ruta absoluta dentro del proyecto
        full_file_path = project_path / file_rel

        # ======================================
        # PROJECT CONTEXT & GENERATE CODE
        # ======================================
        context = get_project_context(prompt)

        response = backend_agent.kickoff(
            f"""
PROJECT CONTEXT:

{context}

====================================

TASK:

{prompt}

====================================

RULES:

- Generate ONLY code
- No explanations
- No markdown
- No talking
- Keep compatibility with existing architecture
- Respect current project structure
"""
        )

        # ======================================
        # SAFE RESPONSE PARSER
        # ======================================
        if response is None:
            return "LLM ERROR: The model returned None. Possible OpenRouter or CrewAI parsing issue."

        code = str(response).strip()

        if not code:
            return "LLM ERROR: Empty code response received."

        # ======================================
        # REMOVE MARKDOWN SANITIZER
        # ======================================
        if "```" in code:
            match = re.search(r"```(?:python)?\s*([\s\S]*?)```", code)
            if match:
                code = match.group(1).strip()
            else:
                code = code.replace("```python", "").replace("```", "").strip()

        # ======================================
        # WRITE FILE
        # ======================================
        full_file_path.parent.mkdir(parents=True, exist_ok=True)
        full_file_path.write_text(code, encoding="utf-8")

        return f"""
FILE GENERATED:

{file_rel}

====================

Archivo guardado correctamente en '{full_file_path}'
"""
    except Exception as e:
        return f"""
FILE GENERATION ERROR:

{str(e)}
"""