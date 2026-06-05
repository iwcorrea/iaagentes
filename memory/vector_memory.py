from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# MODELO DE EMBEDDINGS
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# BASE VECTORIAL
db = Chroma(
    persist_directory="./memory/chroma_db",
    embedding_function=embedding_model
)

# GUARDAR MEMORIA
def save_memory(text):
    db.add_texts([text])
    db.persist()

# BUSCAR MEMORIA
def search_memory(query, k=3):
    results = db.similarity_search(query, k=k)
    return [r.page_content for r in results]