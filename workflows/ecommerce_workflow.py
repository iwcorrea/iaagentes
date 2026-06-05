import json
from crewai import Crew, Task
from agents.director_agent import director_agent
from agents.backend_agent import backend_agent
from agents.frontend_agent import frontend_agent
from agents.qa_agent import qa_agent

def run_ecommerce_workflow(user_prompt):
    # =========================
    # DIRECTOR TASK
    # =========================
    director_task = Task(
        description=f"""
Eres un arquitecto de software. Para el siguiente requerimiento:
"{user_prompt}"

Genera un PLAN JSON con los archivos necesarios (backend y frontend). Incluye:
- main.py
- models.py
- database.py
- routers/__init__.py
- routers/products.py (o similar)
- routers/users.py (si aplica)
- frontend/App.jsx
- otros archivos que consideres esenciales.

Formato obligatorio:
{{
  "files": [
    "backend/main.py",
    "backend/models/product.py",
    "backend/database.py",
    "frontend/App.jsx"
  ]
}}
Devuelve ÚNICAMENTE las llaves del JSON, sin bloques de código ```json ni texto adicional.
""",
        expected_output="JSON puro con la lista de archivos",
        agent=director_agent
    )

    # =========================
    # BACKEND TASK (Optimizada)
    # =========================
    backend_task = Task(
        description=f"""
Eres un generador de código backend. Usa el plan JSON generado por el Director (lista de archivos) para escribir el código completo de cada archivo de backend.

Entrega tu respuesta usando EXACTAMENTE este formato (sin markdown, sin explicaciones):

backend/main.py:::from fastapi import FastAPI
app = FastAPI()
...

backend/database.py:::import sqlalchemy
...

Reglas:
- Cada bloque empieza con la ruta del archivo, seguida de ::: y luego el código en las líneas siguientes.
- NO escribas introducciones ni conclusiones.
- El código debe ser completo y funcional.
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
Eres un generador de frontend. Basándote en el plan del Director, escribe el código del frontend (React).

Entrega tu respuesta usando el mismo formato:
frontend/App.jsx:::import React, {{ useState, useEffect }} from 'react';
...

Reglas:
- Empieza con la ruta y :::
- No uses bloques de markdown.
- Asegúrate de que el código sea moderno y funcional.
""",
        expected_output="Código frontend en formato archivo:::código",
        agent=frontend_agent,
        context=[director_task]
    )

    # =========================
    # QA TASK (con acceso al código generado)
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

    # Extraer salidas y combinarlas
    def get_output(task):
        out = task.output
        return str(out.raw) if hasattr(out, 'raw') else str(out)

    backend_code = get_output(backend_task)
    frontend_code = get_output(frontend_task)
    qa_report = get_output(qa_task)

    # Combinar ambos códigos para que execute_plan los procese
    combined_code = backend_code.strip() + "\n" + frontend_code.strip()
    return combined_code, qa_report