from core.code_executor import (
    run_python_file
)

from core.error_analyzer import (
    analyze_error
)

from agents.repair_agent import (
    repair_agent
)

from tools.custom_tools import (
    write_file,
    read_file
)

# ==========================================
# AUTOREPAIR SYSTEM
# ==========================================

def autorepair(file_path):

    # ======================================
    # EXECUTE FILE
    # ======================================

    result = run_python_file(file_path)

    # ======================================
    # SUCCESS
    # ======================================

    if result["success"]:

        return f"""
CODE EXECUTED SUCCESSFULLY

STDOUT:

{result['stdout']}
"""

    # ======================================
    # ANALYZE ERROR
    # ======================================

    error_context = analyze_error(result)

    # ======================================
    # READ CURRENT FILE
    # ======================================

    current_code = read_file.run(file_path)

    # ======================================
    # REPAIR PROMPT
    # ======================================

    response = repair_agent.kickoff(
        f"""
BROKEN FILE:

{file_path}

====================================

CURRENT CODE:

{current_code}

====================================

ERROR:

{error_context}

====================================

TASK:

Fix the code completely.

RULES:
- Return ONLY fixed code
- No markdown
- No explanations
- Preserve architecture
"""
    )

    fixed_code = str(response).strip()

    # ======================================
    # SANITIZER
    # ======================================

    if "```" in fixed_code:

        import re

        match = re.search(
            r"```(?:python)?\s*([\s\S]*?)```",
            fixed_code
        )

        if match:
            fixed_code = match.group(1).strip()

    # ======================================
    # REWRITE FILE
    # ======================================

    write_result = write_file.run(
        f"{file_path}:::{fixed_code}"
    )

    # ======================================
    # RETEST
    # ======================================

    second_result = run_python_file(file_path)

    return f"""
AUTOREPAIR COMPLETE

==========================

WRITE RESULT:

{write_result}

==========================

FINAL EXECUTION:

SUCCESS: {second_result['success']}

STDOUT:

{second_result['stdout']}

STDERR:

{second_result['stderr']}
"""