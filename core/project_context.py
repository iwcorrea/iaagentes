from memory.vector_memory import (
    search_memory
)

# ==========================================
# GET RELEVANT CONTEXT
# ==========================================

def get_project_context(query):

    results = search_memory(
        query,
        k=5
    )

    return "\n\n".join(results)