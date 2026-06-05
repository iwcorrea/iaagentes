import os
import sys
from dotenv import load_dotenv

# =====================================================================
# 1. MANEJO DE RUTAS Y ENTORNO
# =====================================================================
# Asegurar que Python reconozca la raíz del proyecto para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Cargar variables del entorno (.env) para DeepSeek
load_dotenv()

from configs.logger import logger
from memory.document_loader import load_and_index_pdf
from memory.vector_memory import search_memory

print("=========================================================")
print("🤖 BIENVENIDO AL SISTEMA ORQUESTADOR CENTRAL AI-ECOSYSTEM")
print("=========================================================\n")

def initialize_system():
    """Prepara el entorno, carga conocimientos y valida la infraestructura."""
    logger.info("Iniciando orquestación principal del sistema...")
    
    # ─── PASO A: CARGAR DOCUMENTACIÓN (RAG DOCUMENTAL) ───
    # Si tienes algún PDF con requerimientos dentro de project_knowledge, lo indexamos
    pdf_target = "memory/project_knowledge/requerimientos_ecommerce.pdf"
    
    if os.path.exists(pdf_target):
        logger.info(f"Se detectó documentación técnica en '{pdf_target}'. Indexando...")
        status = load_and_index_pdf(pdf_target)
        logger.info(f"Estado del RAG: {status}")
    else:
        logger.warning(
            f"No se encontró un PDF en '{pdf_target}'. "
            "El sistema operará únicamente con las constantes de memoria locales."
        )

    # ─── PASO B: VERIFICACIÓN DE VARIABLES COMPATIBLES ───
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("DEEPSEEK_BASE_URL"):
        logger.error("Error: Las variables de compatibilidad de DeepSeek no están en el .env")
        sys.exit(1)

def run_pipeline():
    """Ejecuta el flujo modular de agentes."""
    logger.info("Invocando el módulo de workflow automatizado...")
    
    try:
        # Importamos dinámicamente el workflow para que ejecute su lógica interna
        import workflows.ecommerce_workflow
        
    except Exception as e:
        logger.critical(f"El workflow falló drásticamente durante la ejecución: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # 1. Inicializar bases de datos y memorias
    initialize_system()
    
    # 2. Lanzar el debate multiagente con herramientas
    run_pipeline()
