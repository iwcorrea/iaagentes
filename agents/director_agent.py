import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from tools.custom_tools import read_file, run_terminal
from tools.memory_tools import save_memory_tool, search_memory_tool

load_dotenv()

current_model = os.getenv("CURRENT_BRAIN_MODEL", "local-coder")

llm = LLM(
    model=current_model,
    api_key="no-necesita-key-real",
    base_url="http://localhost:4000/v1",
    api_base="http://localhost:4000/v1",
    stop=[]
)

# Cargar tools solo si el modelo las soporta (modos nube e híbrido)
supports_tools = current_model in ("cloud-coder", "hibrido-coder")
agent_tools = [read_file, run_terminal, save_memory_tool, search_memory_tool] if supports_tools else []

director_agent = Agent(
    role="Director IA",
    goal="Coordinar agentes y generar planes JSON válidos con estructura profesional.",
    backstory="""
Eres un arquitecto de software. Tu única misión es generar planes JSON válidos.
NO converses, NO des introducciones, NO uses bloques ```json.

Formato obligatorio:
{
  "project_name": "nombre_del_proyecto",
  "files": [...]
}
Reglas críticas:
- Si el prompt pide "web", "frontend", "página", genera React + Vite, NUNCA React Native o Expo.
- El plan debe incluir backend/main.py, backend/schemas.py, backend/models.py, backend/auth.py, backend/requirements.txt.
- Si hay autenticación JWT, schemas.py debe contener la clase Token.
- Todos los routers deben ser incluidos en main.py.
""",
    llm=llm,
    tools=agent_tools,
    verbose=True
)