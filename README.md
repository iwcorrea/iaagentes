# 🤖 AI-ECOSYSTEM — Arquitecto Autónomo de Software

**Creado por Wilson Correa**

Un ecosistema de agentes de inteligencia artificial que genera aplicaciones web completas a partir de descripciones en lenguaje natural.  
Todo funciona con modelos gratuitos (OpenRouter) y/o un modelo local (Ollama), sin coste de API.

---

## 🧠 ¿Qué hace?

Escribí algo como *"Crear una app de cobro diario con FastAPI y React"* y el sistema:

1. **Valida el prompt** para evitar ambigüedades.
2. **Planifica** la arquitectura (Director IA).
3. **Genera el backend** en Python/FastAPI (Code Generator).
4. **Genera el frontend** en React/Tailwind (Frontend Designer).
5. **Audita el código** buscando errores y vulnerabilidades (QA Auditor).
6. **Repara automáticamente** los problemas encontrados (Repair Agent).
7. **Gestiona dependencias** generando `requirements.txt` y `package.json` (Dependency Manager).
8. **Revisa estáticamente** la integridad del código (CodeReviewer).
9. **Limpia el código** con black, isort y bandit.
10. **Propone mejoras** continuas (MetaAgent).

Todo el proceso es automático y supervisado por el **Orchestrator**, que muestra el progreso en tiempo real.

---

## 🚀 Arranque rápido

### Requisitos
- Python 3.10+
- Node.js 18+
- Git
- (Opcional) Ollama para modelo local

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/iwcorrea/iaagentes.git
cd iaagentes

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno (crear archivo .env)
echo OPENROUTER_API_KEY=tu_clave_de_openrouter > .env

# Iniciar todo con un solo comando
.\start.ps1  # Windows
Luego abrí http://localhost:5173 en tu navegador.

🧰 Estructura del proyecto
text
iaagentes/
├── api/                    # Servidor FastAPI
├── agents/                 # Agentes CrewAI (Director, Backend, Frontend, QA, Repair, Dependency)
├── core/                   # Orquestador, memoria, ejecutor, validador, auditor, revisor
├── workflows/              # Flujo de trabajo CrewAI
├── tools/                  # Herramientas de los agentes
├── memory/                 # Memoria vectorial (ChromaDB)
├── nfrontend/frontend/     # Panel de control React
├── projects/               # Proyectos generados por los agentes
├── start.ps1               # Script de arranque (Windows)
├── start.sh                # Script de arranque (Linux/Mac)
└── settings.json           # Configuración del sistema
🎛️ Panel de control
El panel React incluye:

Chat: crear o modificar proyectos conversando con los agentes.

Proyectos: lista de proyectos generados con nombres editables.

Equipo: visualización en tiempo real del estado de cada agente.

Vista previa: previsualización del proyecto ejecutándose.

Consola: salida de la ejecución del backend.

Configuración: ajuste de modelos, agentes y equipos sin tocar código.

Asistente guiado: creación de proyectos con preguntas personalizadas por tipo de app.

🧠 Modos de cerebro
El sistema soporta tres modos seleccionables desde la interfaz:

Modo	Descripción
🦙 Local	Usa Ollama con qwen2.5-coder:1.5b. Sin límites, sin internet.
☁️ Nube	Usa OpenRouter con modelos gratuitos. Requiere conexión.
🔀 Híbrido	Primero intenta con Ollama; si falla, automáticamente usa la nube.
El modo se selecciona con un selector en el chat antes de enviar el prompt.

🆓 Modelos gratuitos utilizados (modo Nube)
El sistema usa modelos gratuitos a través de OpenRouter, gestionados por LiteLLM:

NVIDIA Nemotron Super 120B

Google Gemma 4 31B

Qwen 3 Coder

Meta Llama 3.3 70B

OpenAI GPT-OSS 120B

Nous Hermes 3 Llama 405B

El proxy LiteLLM maneja automáticamente los fallbacks si un modelo está saturado.

📡 Endpoints principales de la API
Método	Ruta	Descripción
POST	/v1/chat/completions	Enviar prompt y recibir respuesta de los agentes
POST	/api/validate-prompt	Validar un prompt sin generar código
GET	/api/guided-templates	Listar tipos de proyectos guiados
POST	/api/create-guided-project	Crear proyecto con asistente guiado
GET	/projects	Listar proyectos generados
GET	/api/agents	Obtener estado y progreso de los agentes
GET	/api/settings	Obtener configuración del sistema
PUT	/api/settings	Actualizar configuración
🧪 Asistente guiado de proyectos
El panel incluye un asistente que hace preguntas según el tipo de proyecto:

App Web Full-Stack

E-Commerce

API REST

Panel de Administración

Landing Page

Responde las preguntas, previsualizá el prompt generado y los agentes lo construirán con estructura profesional.

🔍 Validaciones automáticas
El sistema incluye múltiples capas de validación para garantizar la calidad del código generado:

PromptIntegrity: valida el prompt antes de enviarlo.

PlanValidator: verifica que el plan JSON del Director sea completo.

ProjectAuditor: audita la estructura del proyecto generado.

CodeReviewer: revisa estáticamente el backend (routers, schemas, imports).

Black + isort + Bandit: formateo, orden y seguridad automáticos.

🛡️ Protecciones
Backup automático antes de cada modificación.

Timeout inteligente por agente (90s).

Reintentos automáticos ante errores de permisos.

Detección de límite diario de OpenRouter (detiene las reparaciones).

Compresión de contexto para no exceder límites de tokens.

Bloqueo de suspensión del PC durante la generación.

🤝 Contribuciones
Este proyecto está en desarrollo activo.
Si querés contribuir, abrí un issue o un pull request en el repositorio.

📄 Licencia
MIT