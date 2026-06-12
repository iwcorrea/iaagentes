"""
Flujo completo de CrewAI con generación paralela de Backend y Frontend.
"""
import asyncio
from crewai import Crew, Task
from agents.director_agent import director_agent
from agents.backend_agent import backend_agent
from agents.frontend_agent import frontend_agent
from agents.qa_agent import qa_agent


def run_ecommerce_workflow(user_prompt, project_context="", is_modification=False):
    """
    Ejecuta el flujo: Director planifica, luego Backend y Frontend generan en paralelo,
    y finalmente QA audita.
    """

    # ─── DIRECTOR ───
    if is_modification:
        director_desc = f"""
Eres un arquitecto de software. El proyecto YA EXISTE y necesita MODIFICACIONES.
CONTEXTO:
{project_context}

SOLICITUD:
"{user_prompt}"

Genera un plan JSON con SOLO los archivos a modificar/crear.
"""
    else:
        director_desc = f"""
Eres un arquitecto de software. Crea un plan JSON para un NUEVO proyecto:
"{user_prompt}"

Incluye backend y frontend según requerimiento.
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
Contexto: {project_context}
Entrega SOLO los archivos que cambian, en formato ruta:::código.
"""
    else:
        backend_desc = f"""
Eres un generador de código backend. CREA el código según el plan del Director.
Entrega en formato ruta:::código. Incluye requirements.txt.
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
Contexto: {project_context}
Entrega SOLO los archivos que cambian, en formato ruta:::código.
"""
    else:
        frontend_desc = f"""
Eres un generador de frontend. CREA el código según el plan del Director.
Entrega en formato ruta:::código. Incluye package.json.
"""

    frontend_task = Task(
        description=frontend_desc,
        expected_output="Código frontend en formato ruta:::código",
        agent=frontend_agent,
        context=[director_task]
    )

    # ─── CREWS SEPARADAS PARA PARALELIZAR ───
    director_crew = Crew(
        agents=[director_agent],
        tasks=[director_task],
        verbose=False
    )

    backend_crew = Crew(
        agents=[backend_agent],
        tasks=[backend_task],
        verbose=False
    )

    frontend_crew = Crew(
        agents=[frontend_agent],
        tasks=[frontend_task],
        verbose=False
    )

    # 1. Ejecutar Director (secuencial, necesario para el plan)
    director_crew.kickoff()

    # 2. Ejecutar Backend y Frontend en paralelo
    async def run_parallel():
        loop = asyncio.get_event_loop()
        backend_future = loop.run_in_executor(None, backend_crew.kickoff)
        frontend_future = loop.run_in_executor(None, frontend_crew.kickoff)
        backend_result, frontend_result = await asyncio.gather(backend_future, frontend_future)
        return backend_result, frontend_result

    try:
        backend_result, frontend_result = asyncio.run(run_parallel())
    except Exception:
        # Fallback secuencial si asyncio falla
        backend_result = backend_crew.kickoff()
        frontend_result = frontend_crew.kickoff()

    # 3. QA sobre el resultado combinado
    def get_output(task_or_crew):
        if hasattr(task_or_crew, 'output'):
            out = task_or_crew.output
        else:
            out = task_or_crew
        if out is None:
            return ""
        return str(out.raw) if hasattr(out, 'raw') else str(out)

    backend_code = get_output(backend_result)
    frontend_code = get_output(frontend_result)

    combined = backend_code.strip()
    if frontend_code.strip():
        combined += "\n" + frontend_code.strip()

    qa_task = Task(
        description="Revisa el código generado y genera un informe de auditoría.",
        expected_output="Informe de auditoría",
        agent=qa_agent
    )
    qa_crew = Crew(agents=[qa_agent], tasks=[qa_task], verbose=False)
    qa_crew.kickoff()
    qa_report = get_output(qa_crew)

    return combined or "backend/main.py:::print('Sin cambios')", qa_report