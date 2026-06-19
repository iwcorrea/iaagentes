import os
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv()

def get_llm():
    current_model = os.getenv("CURRENT_BRAIN_MODEL", "local-coder")
    return LLM(
        model=current_model,
        api_key="no-necesita-key-real",
        base_url="http://localhost:4000/v1",
        api_base="http://localhost:4000/v1",
        stop=[]
    )

def get_tools():
    current_model = os.getenv("CURRENT_BRAIN_MODEL", "local-coder")
    if current_model in ("cloud-coder", "hibrido-coder"):
        from tools.custom_tools import read_file, run_terminal
        from tools.memory_tools import save_memory_tool, search_memory_tool
        return [read_file, run_terminal, save_memory_tool, search_memory_tool]
    return []

qa_agent = Agent(
    role="QA Auditor",
    goal="Detectar errores, vulnerabilidades, malas prácticas, y problemas de sintaxis (como archivos .js con JSX).",
    backstory="""
Especialista senior en debugging, QA, seguridad.
Reglas adicionales:
- Revisar que los archivos React tengan extensión .jsx si contienen JSX.
- Verificar imports relativos y su existencia.
- Detectar secretos hardcodeados.
- Generar informe claro con Problema, Impacto, Solución.
""",
    llm=get_llm(),
    tools=get_tools(),
    verbose=True
)