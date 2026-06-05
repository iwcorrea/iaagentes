# ==========================================
# ANALYZE ERRORS
# ==========================================

def analyze_error(execution_result):

    if execution_result["success"]:

        return None

    return f"""
PYTHON EXECUTION FAILED

STDERR:

{execution_result['stderr']}

STDOUT:

{execution_result['stdout']}
"""