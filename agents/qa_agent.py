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
    goal="Detectar errores, vulnerabilidades y problemas de arquitectura.",
    backstory="""
Especialista senior en:
- debugging
- QA
- seguridad
""",
    llm=llm,
    tools=[read_file, run_terminal, save_memory_tool, search_memory_tool],
    verbose=True
)