import re

from tools.custom_tools import (
    write_file,
    run_terminal
)

# =========================
# EXECUTE ACTIONS
# =========================

def execute_actions(text):

    results = []

    # =========================
    # WRITE FILE
    # =========================

    write_pattern = r"WRITE_FILE:(.*?):::([\s\S]*?)(?=WRITE_FILE:|RUN_TERMINAL:|$)"

    write_matches = re.findall(
        write_pattern,
        text
    )

    for path, content in write_matches:

        tool_input = f"""
        {path.strip()}:::{content.strip()}
        """

        result = write_file.run(
            tool_input
        )

        results.append(result)

    # =========================
    # RUN TERMINAL
    # =========================

    terminal_pattern = r"RUN_TERMINAL:(.*)"

    terminal_matches = re.findall(
        terminal_pattern,
        text
    )

    for command in terminal_matches:

        result = run_terminal.run(
            command.strip()
        )

        results.append(result)

    # =========================
    # NO ACTIONS DETECTED
    # =========================

    if not results:

        return """
        ERROR:

        El modelo no generó acciones ejecutables.

        Debe usar:

        WRITE_FILE:
        ruta:::contenido

        o:

        RUN_TERMINAL:
        comando
        """

    return "\n".join(results)
