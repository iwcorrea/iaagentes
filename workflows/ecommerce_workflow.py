"""
Flujo completo de CrewAI para generación y modificación de proyectos.
"""
from crewai import Crew, Task
from agents.director_agent import director_agent
from agents.backend_agent import backend_agent
from agents.frontend_agent import frontend_agent
from agents.qa_agent import qa_agent


def run_ecommerce_workflow(user_prompt, project_context="", is_modification=False):
    """
    Si is_modification es True, los agentes reciben el contexto completo del proyecto
    y se espera que modifiquen solo los archivos necesarios.
    """

    # ─── DIRECTOR ───
    if is_modification:
        director_desc = f"""
Eres un arquitecto de software. El siguiente proyecto YA EXISTE y necesita ser MODIFICADO.
CONTEXTO DEL PROYECTO (archivos actuales):
{project_context}

SOLICITUD DE MODIFICACIÓN:
"{user_prompt}"

Genera un plan JSON con SOLO los archivos que deben MODIFICARSE o CREARSE.
Devuelve ÚNICAMENTE las llaves del JSON.
"""
    else:
        director_desc = f"""
Eres un arquitecto de software. Crea un plan JSON para un NUEVO proyecto:
"{user_prompt}"

Incluye backend y frontend según el requerimiento.
Devuelve ÚNICAMENTE las llaves del JSON.
"""

    director_task = Task(
        description=director_desc,
        expected_output="JSON con lista de archivos",
        agent=director_agent
    )

    # ─── BACKEND ───
    if is_modification:
        backend_desc = f"""
Eres un generador de código. MODIFICA el proyecto existente según el plan del Director.
Contexto del proyecto:
{project_context}

Entrega SOLO los archivos que necesitan cambios, usando el formato ruta:::código.
El código debe ser el archivo COMPLETO (no solo la parte modificada).
"""
    else:
        backend_desc = f"""
Eres un generador de código. Crea el backend según el plan del Director.
Usa el formato ruta:::código. Incluye requirements.txt.
"""

    backend_task = Task(
        description=backend_desc,
        expected_output="Código en formato ruta:::código",
        agent=backend_agent,
        context=[director_task]
    )

    # ─── FRONTEND ───
    if is_modification:
        frontend_desc = f"""
Eres un generador de frontend. MODIFICA el proyecto existente según el plan del Director.
Contexto del proyecto:
{project_context}

Entrega SOLO los archivos que necesitan cambios, usando el formato ruta:::código.
"""
    else:
        frontend_desc = f"""
Eres un generador de frontend. Crea el frontend según el plan del Director.
Usa el formato ruta:::código. Incluye package.json.
"""

    frontend_task = Task(
        description=frontend_desc,
        expected_output="Código frontend en formato ruta:::código",
        agent=frontend_agent,
        context=[director_task]
    )

    # ─── QA ───
    qa_task = Task(
        description="Revisa el código generado y genera un informe de auditoría con Problema, Impacto, Solución.",
        expected_output="Informe de auditoría",
        agent=qa_agent,
        context=[backend_task, frontend_task]
    )

    # ─── CREW ───
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
        return str(out.raw) if hasattr(out, 'raw') else str(out)

    backend_code = get_output(backend_task)
    frontend_code = get_output(frontend_task)
    qa_report = get_output(qa_task)

    combined = backend_code.strip()
    if frontend_code.strip():
        combined += "\n" + frontend_code.strip()

    if not combined:
        combined = "backend/main.py:::print('Sin cambios generados')"

    return combined, qa_report