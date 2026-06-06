import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from tools.custom_tools import read_file, write_file
from tools.memory_tools import save_memory_tool, search_memory_tool

load_dotenv()

llm = LLM(
    model="gratuito-fallback",
    api_key="no-necesita-key-real",
    base_url="http://localhost:4000/v1",
    api_base="http://localhost:4000/v1",
    stop=[]
)

frontend_agent = Agent(
    role="Frontend Designer",
    goal="Diseñar interfaces modernas y responsive.",
    backstory="""
Especialista frontend experto en:
- React
- Tailwind
- UX/UI
- Usar formato path:::code para entregar archivos
""",
    llm=llm,
    tools=[read_file, write_file, save_memory_tool, search_memory_tool],
    verbose=True
)