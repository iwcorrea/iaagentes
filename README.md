# 🤖 AI-ECOSYSTEM — Arquitecto Autónomo de Software

**Creado por Wilson Correa**

Un ecosistema de agentes de inteligencia artificial que genera aplicaciones web completas a partir de descripciones en lenguaje natural.  
Todo funciona con modelos gratuitos, sin coste de API.

---

## 🧠 ¿Qué hace?

Escribí algo como *"Crear una app de cobro diario con FastAPI y React"* y el sistema:

1. **Planifica** la arquitectura (Director IA).
2. **Genera el backend** en Python/FastAPI (Code Generator).
3. **Genera el frontend** en React/Tailwind (Frontend Designer).
4. **Audita el código** buscando errores y vulnerabilidades (QA Auditor).
5. **Repara automáticamente** los problemas encontrados (Repair Agent).
6. **Gestiona dependencias** generando `requirements.txt` y `package.json` (Dependency Manager).

Todo el proceso es automático y supervisado por un **MetaAgent** que propone mejoras continuas.

---

## 🚀 Arranque rápido

### Requisitos
- Python 3.10+
- Node.js 18+
- Git

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
