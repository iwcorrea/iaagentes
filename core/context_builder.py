from core.project_scanner import (
    scan_project
)

from memory.vector_memory import (
    save_memory
)

# ==========================================
# BUILD PROJECT CONTEXT
# ==========================================

def build_project_context():

    files = scan_project()

    total = 0

    for file_data in files:

        text = f"""

FILE:

{file_data['path']}

CONTENT:

{file_data['content']}
"""

        save_memory(text)

        total += 1

    return f"""
PROJECT INDEXED SUCCESSFULLY

FILES INDEXED:
{total}
"""