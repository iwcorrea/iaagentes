import json

from agents.director_agent import (
    director_agent
)

from core.file_generator import (
    generate_file
)

from core.autorepair import (
    autorepair
)

# ==========================================
# PROJECT ORCHESTRATOR
# ==========================================

def orchestrate_project(user_prompt):

    # ======================================
    # CREATE PLAN
    # ======================================

    response = director_agent.kickoff(
        f"""
You are a software architect.

Create a JSON execution plan.

USER REQUEST:

{user_prompt}

RULES:

- ONLY return valid JSON
- No markdown
- No explanations

FORMAT:

{{
  "files": [
    {{
      "path": "workspace/backend/main.py",
      "task": "Create FastAPI app"
    }}
  ]
}}
"""
    )

    # ======================================
    # PARSE PLAN
    # ======================================

    try:

        cleaned = str(response).strip()

        if "```" in cleaned:

            import re

            match = re.search(
                r"```(?:json)?\s*([\s\S]*?)```",
                cleaned
            )

            if match:
                cleaned = match.group(1).strip()

        plan = json.loads(cleaned)

    except Exception as e:

        return f"""
PLAN PARSE ERROR

{str(e)}

RAW RESPONSE:

{response}
"""

    # ======================================
    # EXECUTION RESULTS
    # ======================================

    results = []

    files = plan.get("files", [])

    # ======================================
    # GENERATE FILES
    # ======================================

    for file_data in files:

        path = file_data.get("path")
        task = file_data.get("task")

        if not path or not task:
            continue

        generation_prompt = f"""
Create:

{path}

TASK:

{task}
"""

        generation_result = generate_file(
            generation_prompt
        )

        repair_result = autorepair(
            path
        )

        results.append({

            "file": path,

            "generation": generation_result,

            "repair": repair_result
        })

    return results