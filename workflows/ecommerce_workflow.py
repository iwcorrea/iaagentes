"""
Flujo completo de CrewAI para generación de proyectos.
Orquesta a los 5 agentes: director, backend, frontend, QA y repair.
Fuerza la generación de archivos obligatorios para producción.
"""

from crewai import Crew, Task
from agents.director_agent import director_agent
from agents.backend_agent import backend_agent
from agents.frontend_agent import frontend_agent
from agents.qa_agent import qa_agent


def run_ecommerce_workflow(user_prompt):
    """
    Ejecuta el flujo completo de agentes CrewAI.
    Retorna una tupla (codigo_combinado, informe_qa).
    """

    # =========================
    # DIRECTOR TASK
    # =========================
    director_task = Task(
        description=f"""
Eres un arquitecto de software. Para el siguiente requerimiento:
"{user_prompt}"

Genera un PLAN JSON con TODOS los archivos necesarios (backend y frontend).
Incluye OBLIGATORIAMENTE:
- backend/main.py
- backend/database.py
- backend/models.py
- backend/schemas.py
- backend/auth.py (con SECRET_KEY de variables de entorno)
- backend/routers/__init__.py
- backend/routers/auth.py
- backend/routers/payments.py (o similar)
- backend/requirements.txt
- frontend/package.json
- frontend/src/App.jsx
- frontend/src/index.jsx
- manual.txt

Formato obligatorio:
{{
  "files": [
    "backend/main.py",
    "backend/database.py",
    "backend/models.py",
    "backend/schemas.py",
    "backend/auth.py",
    "backend/routers/__init__.py",
    "backend/routers/auth.py",
    "backend/routers/payments.py",
    "backend/requirements.txt",
    "frontend/package.json",
    "frontend/src/App.jsx",
    "frontend/src/index.jsx",
    "manual.txt"
  ]
}}
Devuelve ÚNICAMENTE las llaves del JSON, sin bloques de código ```json ni texto adicional.
""",
        expected_output="JSON puro con la lista de archivos obligatorios",
        agent=director_agent
    )

    # =========================
    # BACKEND TASK (con reglas estrictas)
    # =========================
    backend_task = Task(
        description=f"""
Eres un generador de código backend. Usa el plan JSON del Director para escribir el código completo de CADA archivo listado.

Entrega tu respuesta usando EXACTAMENTE este formato (sin markdown, sin explicaciones):

backend/main.py:::from fastapi import FastAPI
app = FastAPI()
...

backend/database.py:::from sqlalchemy import create_engine
...

backend/requirements.txt:::fastapi
uvicorn
sqlalchemy
python-jose[cryptography]
passlib[bcrypt]
python-multipart
python-dotenv

Reglas de producción obligatorias:
- Usa variables de entorno para SECRET_KEY, DATABASE_URL (nunca hardcodees secretos).
- Las rutas de autenticación deben ser /auth/register, /auth/token, /auth/me.
- Implementa roles (admin, cobrador) y protege los endpoints con dependencias.
- Genera requirements.txt con todas las dependencias necesarias.
- El código debe ser completo, funcional y listo para ejecutar con uvicorn.
- NO uses bloques de markdown.
- Respeta ESTRICTAMENTE el formato ruta:::código para cada archivo.
""",
        expected_output="Código estructurado en formato ruta:::código",
        agent=backend_agent,
        context=[director_task]
    )

    # =========================
    # FRONTEND TASK
    # =========================
    frontend_task = Task(
        description=f"""
Eres un generador de frontend. Basándote en el plan del Director, escribe el código de TODOS los archivos del frontend.

Entrega tu respuesta usando el mismo formato:
frontend/package.json:::{{...}}
frontend/src/App.jsx:::import React from 'react';
...

Reglas obligatorias:
- Siempre genera frontend/package.json con react, react-dom, react-router-dom, axios, tailwindcss, vite.
- Nunca hardcodees roles ('admin', 'collector') en el frontend. Los roles deben venir del JWT.
- Usa variables de entorno (VITE_API_URL) para la URL del backend.
- Implementa manejo de errores con try/catch, NO uses alert().
- Usa localStorage solo para el token, con cuidado de XSS.
- Respeta ESTRICTAMENTE el formato ruta:::código para cada archivo.
""",
        expected_output="Código frontend en formato archivo:::código",
        agent=frontend_agent,
        context=[director_task]
    )

    # =========================
    # QA TASK
    # =========================
    qa_task = Task(
        description="""
Revisa el código generado (backend y frontend) que se te ha pasado en el contexto.
Detecta errores, vulnerabilidades, malas prácticas y problemas de arquitectura.
Genera un informe claro con:
- Problema
- Impacto
- Solución propuesta
""",
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

    # Extraer salidas
    def get_output(task):
        """Extrae el texto de salida de una tarea CrewAI."""
        out = task.output
        if out is None:
            return ""
        if hasattr(out, 'raw'):
            return str(out.raw).strip()
        return str(out).strip()

    backend_code = get_output(backend_task)
    frontend_code = get_output(frontend_task)
    qa_report = get_output(qa_task)

    # Combinar código backend + frontend para execute_plan
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