import os
import logging
from logging.handlers import RotatingFileHandler

# Definir la ruta de la carpeta de logs en la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Crear la carpeta logs si no existe de forma automática
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "system.log")

# Configuración del formato de los mensajes
log_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Configurar el manejador para escribir en el archivo (Rota al llegar a 5MB)
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8"
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Configurar el manejador para mostrar los mensajes en la terminal en vivo
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Inicializar el objeto logger global
logger = logging.getLogger("AI-ECOSYSTEM-LOGGER")
logger.setLevel(logging.INFO)

# Evitar duplicar registros agregando los manejadores de forma limpia
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
