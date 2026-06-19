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
    llm=get_llm(),
    tools=get_tools(),
    verbose=True
)