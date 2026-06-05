from crewai.tools import tool

from memory.vector_memory import (
    save_memory,
    search_memory
)

# =========================
# SAVE MEMORY TOOL
# =========================

@tool("Save Memory")
def save_memory_tool(text: str):

    """
    Guarda información importante
    en la memoria vectorial.
    """

    save_memory(text)

    return "Memoria guardada correctamente."

# =========================
# SEARCH MEMORY TOOL
# =========================

@tool("Search Memory")
def search_memory_tool(query: str):

    """
    Busca información relevante
    en memoria vectorial.
    """

    results = search_memory(query)

    return "\n".join(results)