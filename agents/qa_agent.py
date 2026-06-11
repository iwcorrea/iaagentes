import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from tools.custom_tools import read_file, run_terminal
from tools.memory_tools import save_memory_tool, search_memory_tool

load_dotenv()

llm = LLM(
    model="gratuito-fallback",
    api_key="no-necesita-key-real",
    base_url="http://localhost:4000/v1",
    api_base="http://localhost:4000/v1",
    stop=[]
)

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
    llm=llm,
    tools=[read_file, run_terminal, save_memory_tool, search_memory_tool],
    verbose=True
)