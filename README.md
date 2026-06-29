# 🧠 AI-ECOSYSTEM — Arquitecto Autónomo de Software

Ecosistema de agentes CrewAI que genera aplicaciones web completas a partir de prompts en lenguaje natural, usando modelos gratuitos de OpenRouter u Ollama (local). Todo funciona con coste cero.

## 🚀 Estado actual (27/Jun/2026)

### ✅ Mejoras completadas
- **Orquestador modular con 5 fases:** generación, auditoría, dependencias, tests, despliegue.
- **ProjectMemory:** persistencia del estado del proyecto, decisiones de diseño, issues de auditoría, y manifiesto de archivos con hash para evitar alucinaciones.
- **Documentos `.md` por proyecto:** los agentes reciben instrucciones específicas desde `docs/` en cada proyecto (frontmatter YAML con target_agents, priority, tags).
- **Sistema de Skills polimórfico:** carga skills desde archivos `.skill.json`, `.yaml`, `.py` y directorios (compatible con repos de la comunidad).
- **Integración con JennGen:** el skill `jenngen` convierte pseudocódigo en HTML/CSS/JS real usando modelos locales o de OpenAI.
- **Extracción robusta de código:** el extractor JSON balanceado captura código incluso cuando el LLM usa backticks o formato irregular.
- **Panel React moderno:** chat persistente, selector de modelo (local/nube/híbrido), barra de progreso granular, explorador de archivos con syntax highlighting, gestor de documentos Markdown.
- **Validación sintáctica automática:** descarta archivos Python con errores y permite reintentar.
- **Reanudación automática:** si una fase falla (por rate‑limit o timeout), el estado se guarda y se puede continuar más tarde.

### 🔧 En desarrollo
- **Editor Markdown enriquecido** para la pestaña Docs.
- **Mejora de UI:** vista previa de código con resaltado, panel de configuración avanzado.
- **Descarga de skills desde GitHub** con actualización automática.

## 🧩 Estructura del proyecto

```text
iaagentes/
├── api/                  # FastAPI (endpoint principal + routers)
├── agents/               # Agentes CrewAI (director, backend, frontend, etc.)
├── core/                 # Orquestador, fases, memoria, skills, loaders
├── tools/                # Herramientas externas (Jenngen, etc.)
├── skills/               # Skills descargables o locales (.skill.json)
├── nfrontend/frontend/   # Panel React con Vite + Tailwind
├── tests/                # Pruebas unitarias
├── litellm_config.yaml   # Configuración de modelos gratuitos
├── start.ps1             # Script de arranque
└── requirements.txt
🛠️ Configuración rápida
Cloná el repositorio

bash
git clone https://github.com/iwcorrea/iaagentes.git
cd iaagentes
Creá y activá el entorno virtual

bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
Iniciá el ecosistema

bash
.\start.ps1
Respondé s si querés usar el modelo local (Ollama) o n si solo vas a usar OpenRouter.

Abrí el frontend en http://localhost:5173

🧪 Cómo generar un proyecto
Escribí tu prompt en el chat. Ejemplo:

text
Crear proyecto "TestBackend" con:
- FastAPI + SQLite
- Modelo Producto (id, nombre, precio)
- CRUD básico en router /productos
- main.py, database.py, requirements.txt
Solo backend, sin frontend, sin tests.
Seleccioná el modelo deseado (Local, Nube o Híbrido).

Presioná Crear. El progreso se mostrará en tiempo real.

Los archivos aparecerán en la pestaña Explorador y en projects/TestBackend/.

🧠 Skills
Colocá archivos .skill.json en la carpeta skills/.

Ejemplo: skills/mi-skill.skill.json

json
{
  "name": "mi-skill",
  "role": "backend",
  "goal": "Generar código FastAPI optimizado",
  "backstory": "Experto en FastAPI y SQLAlchemy..."
}
La pestaña Skills los listará automáticamente.

Si un skill tiene el mismo nombre o rol que un agente, se usará en lugar del agente por defecto.

El skill jenngen (incluido) mejora la generación de frontend usando la herramienta JennGen.

📚 Documentos por proyecto
Cada proyecto puede tener una carpeta docs/ con archivos .md que guían a los agentes.
Ejemplo (docs/backend-instructions.md):

markdown
---
target_agents: [backend]
priority: high
---

## Instrucciones para el Backend
- Usá FastAPI con SQLAlchemy y SQLite.
- Implementá autenticación JWT con hashlib.
La pestaña Docs permite editar estos archivos directamente en la interfaz.

⚙️ Modelos disponibles
Modelo	Descripción
local-coder	Ollama local (qwen2.5-coder:1.5b)
cloud-coder	OpenRouter gratuito (Nemotron 120B, Gemma, etc.)
hibrido-coder	Local + fallback a nube
📄 Licencia
MIT

text

---

Probá el nuevo `SkillsPanel.jsx` y fijate qué aparece en "Respuesta del servidor".  
Con eso arreglamos el problema de skills y luego seguimos con JennGen y el editor Markdown enriquecido.