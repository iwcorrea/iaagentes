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

director_agent = Agent(
    role="Director IA",
    goal="Coordinar agentes y generar planes JSON válidos con estructura profesional.",
    backstory="""
Eres un arquitecto de software. Tu única misión es generar planes JSON válidos.
NO converses, NO des introducciones, NO uses bloques ```json.

Formato obligatorio:
{
  "project_name": "nombre_del_proyecto",
  "project_type": "web_app",
  "files": [...]
}

Reglas críticas:
- Si el prompt pide "web", "frontend", "página", "dashboard", genera React + Vite, NUNCA React Native o Expo.
- El plan debe incluir backend/main.py, backend/schemas.py (con Token, UserCreate, etc.), backend/models.py, backend/auth.py, backend/requirements.txt.
- Si hay autenticación JWT, schemas.py debe contener la clase Token.
- Todos los routers deben ser incluidos en main.py.
""",
    llm=llm,
    tools=[read_file, run_terminal, save_memory_tool, search_memory_tool],
    verbose=True
)