from crewai.tools import tool
from memory.vector_memory import get_vector_memory

@tool("save_memory")
def save_memory_tool(content: str, metadata: str = "{}") -> str:
    """
    Guarda información en la memoria vectorial del ecosistema.
    Args:
        content: Texto a guardar.
        metadata: JSON string con metadatos adicionales.
    """
    import json
    try:
        meta = json.loads(metadata) if metadata else {}
    except json.JSONDecodeError:
        meta = {"raw": metadata}
    memory = get_vector_memory()
    success = memory.add_document(content, meta)
    if success:
        return "✅ Memoria guardada correctamente."
    return "❌ No se pudo guardar en la memoria vectorial."

@tool("search_memory")
def search_memory_tool(query: str, k: int = 5) -> str:
    """
    Busca información relevante en la memoria vectorial.
    Args:
        query: Consulta de búsqueda.
        k: Número de resultados a devolver.
    """
    memory = get_vector_memory()
    results = memory.search(query, k=k)
    if not results:
        return "🔍 No se encontraron resultados en la memoria."
    output = []
    for i, r in enumerate(results, 1):
        preview = r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"]
        output.append(f"{i}. [{r['score']:.2f}] {preview}")
    return "\n".join(output)