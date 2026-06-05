"""
Memoria vectorial para búsqueda semántica en el ecosistema.
Implementa lazy loading para no bloquear el arranque si hay
problemas con sentence-transformers o chromadb.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any

# ------------------------------------------------------------------
#  LAZY LOADING: no importamos HuggingFaceEmbeddings ni Chroma aquí
# ------------------------------------------------------------------

class VectorMemory:
    """
    Memoria vectorial persistente basada en ChromaDB.
    Se inicializa bajo demanda para evitar errores en el arranque.
    """

    def __init__(self, persist_path: Optional[str] = None):
        self._persist_path = str(Path(persist_path or "memory_db").resolve())
        self._db = None
        self._embedding_model = None
        self._initialized = False

    def _ensure_initialized(self):
        """Inicializa la base de datos vectorial solo cuando se necesita."""
        if self._initialized:
            return
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            from langchain_chroma import Chroma

            self._embedding_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': False}
            )
            self._db = Chroma(
                collection_name="ecosystem_memory",
                embedding_function=self._embedding_model,
                persist_directory=self._persist_path
            )
            self._initialized = True
            print("[VECTOR_MEMORY] ChromaDB inicializado correctamente.")
        except Exception as e:
            print(f"[VECTOR_MEMORY] No se pudo inicializar ChromaDB: {e}")
            print("[VECTOR_MEMORY] La búsqueda semántica no estará disponible.")
            self._initialized = False

    def add_document(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        """Añade un documento a la memoria vectorial."""
        self._ensure_initialized()
        if not self._initialized:
            return False
        try:
            self._db.add_texts(texts=[text], metadatas=[metadata or {}])
            self._db.persist()
            return True
        except Exception as e:
            print(f"[VECTOR_MEMORY] Error al añadir documento: {e}")
            return False

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Busca documentos relevantes por similitud semántica."""
        self._ensure_initialized()
        if not self._initialized:
            return []
        try:
            results = self._db.similarity_search_with_score(query, k=k)
            return [
                {"content": doc.page_content, "metadata": doc.metadata, "score": score}
                for doc, score in results
            ]
        except Exception as e:
            print(f"[VECTOR_MEMORY] Error en búsqueda: {e}")
            return []

    def clear(self) -> bool:
        """Elimina todos los documentos de la colección."""
        self._ensure_initialized()
        if not self._initialized:
            return False
        try:
            self._db.delete_collection()
            self._initialized = False
            return True
        except Exception as e:
            print(f"[VECTOR_MEMORY] Error al limpiar: {e}")
            return False


# Instancia global para todo el ecosistema
_global_memory: Optional[VectorMemory] = None

def get_vector_memory() -> VectorMemory:
    """Devuelve la instancia global de VectorMemory."""
    global _global_memory
    if _global_memory is None:
        _global_memory = VectorMemory()
    return _global_memory