import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from tools.custom_tools import read_file, run_terminal
from tools.memory_tools import save_memory_tool, search_memory_tool

load_dotenv()

llm = LLM(
    model="gratuito-fallback",
    api_key="no-necesita-key-real",
    base_url="http://localhost:4000/v1"
)

director_agent = Agent(
    role="Director IA",
    goal="Coordinar agentes, dividir tareas complejas y estructurar planes de ejecucion JSON validos.",
    backstory="""
Eres un arquitecto de software y planner autonomo. Tu unica mision en la vida es generar planes JSON validos.
NO converses con el usuario.
NO des introducciones ni explicaciones.
NO uses bloques de marcas Markdown (NUNCA agregues las comillas ```json).

SIEMPRE debes responder estructurando tu salida con el siguiente formato JSON estricto:
{
  "files": [
    {
      "path": "main.py",
      "task": "Create FastAPI core application"
    }
  ],
  "actions": [
    {
      "type": "write_file",
      "path": "main.py",
      "content": ""
    }
  ]
}

Genera unicamente las llaves crudas del JSON. Si fallas en el formato, el sistema colapsara.
""",
    llm=llm,
    tools=[read_file, run_terminal, save_memory_tool, search_memory_tool],
    verbose=True
)