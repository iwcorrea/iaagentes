import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from memory.vector_memory import save_memory
from configs.logger import logger

def load_and_index_pdf(pdf_path: str):
    """Lee un archivo PDF, lo fragmenta y lo guarda automáticamente en ChromaDB."""
    if not os.path.exists(pdf_path):
        logger.error(f"El archivo PDF no existe en la ruta: {pdf_path}")
        return f"Error: No se encontró el archivo {pdf_path}"

    try:
        logger.info(f"Cargando documento PDF: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()

        # Dividir el texto en fragmentos óptimos para el modelo de embeddings
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(docs)

        logger.info(f"Fragmentado con éxito: {len(chunks)} fragmentos generados. Guardando en memoria...")

        # Indexar cada fragmento en tu base de datos de ChromaDB
        for chunk in chunks:
            save_memory(chunk.page_content)

        logger.info(f"¡Éxito! Documento {pdf_path} indexado en ChromaDB correctamente.")
        return f"Éxito: {len(chunks)} fragmentos indexados correctamente."

    except Exception as e:
        logger.error(f"Error procesando el PDF: {str(e)}")
        return f"Error: {str(e)}"
