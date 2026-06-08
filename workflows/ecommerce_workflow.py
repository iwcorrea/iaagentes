"""
Flujo completo de CrewAI para generación de proyectos.
Orquesta a los 5 agentes: director, backend, frontend, QA y repair.
Soporta creación desde cero y modificación con contexto.
"""

from crewai import Crew, Task
from agents.director_agent import director_agent
from agents.backend_agent import backend_agent
from agents.frontend_agent import frontend_agent
from agents.qa_agent import qa_agent


def run_ecommerce_workflow(user_prompt, project_context=""):
    """
    Ejecuta el flujo completo de agentes CrewAI.
    Retorna una tupla (codigo_combinado, informe_qa).
    Si project_context tiene contenido, es una modificación.
    """

    is_modification = bool(project_context and project_context.strip())

    # =========================
    # DIRECTOR TASK
    # =========================
    if is_modification:
        director_description = f"""
Eres un arquitecto de software. El siguiente proyecto YA EXISTE y necesita ser MODIFICADO.
CONTEXTO DEL PROYECTO ACTUAL:
{project_context}

PETICIÓN DE MODIFICACIÓN:
"{user_prompt}"

Genera un PLAN JSON con SOLO los archivos que deben MODIFICARSE o CREARSE.
No incluyas archivos que no necesiten cambios.
Formato obligatorio:
{{
  "files": [
    "backend/main.py",
    "backend/models/product.py"
  ]
}}
Devuelve ÚNICAMENTE las llaves del JSON, sin bloques de código ```json ni texto adicional.
"""
    else:
        director_description = f"""
Eres un arquitecto de software. Para el siguiente requerimiento:
"{user_prompt}"

Genera un PLAN JSON con TODOS los archivos necesarios (backend y frontend).
Incluye OBLIGATORIAMENTE:
- backend/main.py
- backend/database.py
- backend/models.py
- backend/schemas.py
- backend/auth.py
- backend/routers/__init__.py
- backend/routers/auth.py
- backend/routers/payments.py
- backend/requirements.txt
- frontend/package.json
- frontend/src/App.jsx
- frontend/src/index.jsx
- manual.txt

Formato obligatorio:
{{
  "files": [
    "backend/main.py",
    "backend/database.py"
  ]
}}
Devuelve ÚNICAMENTE las llaves del JSON, sin bloques de código ```json ni texto adicional.
"""

    director_task = Task(
        description=director_description,
        expected_output="JSON puro con la lista de archivos",
        agent=director_agent
    )

    # =========================
    # BACKEND TASK
    # =========================
    if is_modification:
        backend_description = f"""
Eres un generador de código backend. MODIFICA el proyecto existente según el plan del Director.
CONTEXTO DEL PROYECTO:
{project_context}

Entrega tu respuesta usando EXACTAMENTE este formato (sin markdown, sin explicaciones):
backend/main.py:::código completo del archivo modificado

Reglas:
- Solo genera código para los archivos que necesitan cambios.
- El código debe ser el archivo COMPLETO (no solo la parte modificada).
- Usa variables de entorno para SECRET_KEY, DATABASE_URL.
- Respeta ESTRICTAMENTE el formato ruta:::código.
"""
    else:
        backend_description = f"""
Eres un generador de código backend. Usa el plan JSON del Director para escribir el código completo de CADA archivo listado.

Entrega tu respuesta usando EXACTAMENTE este formato (sin markdown, sin explicaciones):
backend/main.py:::from fastapi import FastAPI
app = FastAPI()
...

Reglas de producción obligatorias:
- Usa variables de entorno para SECRET_KEY, DATABASE_URL.
- Las rutas de autenticación deben ser /auth/register, /auth/token, /auth/me.
- Genera requirements.txt con todas las dependencias necesarias.
- El código debe ser completo, funcional y listo para ejecutar con uvicorn.
- NO uses bloques de markdown.
- Respeta ESTRICTAMENTE el formato ruta:::código para cada archivo.
"""

    backend_task = Task(
        description=backend_description,
        expected_output="Código estructurado en formato ruta:::código",
        agent=backend_agent,
        context=[director_task]
    )

    # =========================
    # FRONTEND TASK
    # =========================
    frontend_description = f"""
Eres un generador de frontend. Basándote en el plan del Director, escribe el código del frontend (React).

Entrega tu respuesta usando el mismo formato:
frontend/package.json:::{{...}}
frontend/src/App.jsx:::import React from 'react';
...

Reglas obligatorias:
- Siempre genera frontend/package.json con react, react-dom, react-router-dom, axios, tailwindcss, vite.
- Nunca hardcodees roles en el frontend. Los roles deben venir del JWT.
- Usa variables de entorno (VITE_API_URL) para la URL del backend.
- Implementa manejo de errores con try/catch, NO uses alert().
- Respeta ESTRICTAMENTE el formato ruta:::código para cada archivo.
"""

    frontend_task = Task(
        description=frontend_description,
        expected_output="Código frontend en formato archivo:::código",
        agent=frontend_agent,
        context=[director_task]
    )

    # =========================
    # QA TASK
    # =========================
    qa_task = Task(
        description="Revisa el código generado (backend y frontend) que se te ha pasado en el contexto. Detecta errores, vulnerabilidades, malas prácticas y problemas de arquitectura. Genera un informe claro con: Problema, Impacto, Solución propuesta.",
        expected_output="Informe de auditoría técnica",
        agent=qa_agent,
        context=[backend_task, frontend_task]
    )

    # =========================
    # CREW
    # =========================
    crew = Crew(
        agents=[director_agent, backend_agent, frontend_agent, qa_agent],
        tasks=[director_task, backend_task, frontend_task, qa_task],
        verbose=True
    )

    crew.kickoff()

    def get_output(task):
        out = task.output
        if out is None:
            return ""
        if hasattr(out, 'raw'):
            return str(out.raw).strip()
        return str(out).strip()

    backend_code = get_output(backend_task)
    frontend_code = get_output(frontend_task)
    qa_report = get_output(qa_task)

    combined_code = ""
    if backend_code:
        combined_code += backend_code
    if frontend_code:
        if combined_code:
            combined_code += "\n"
        combined_code += frontend_code

    if not combined_code:
        combined_code = "backend/main.py:::print('Error: no se generó código')"

    return combined_code, qa_report