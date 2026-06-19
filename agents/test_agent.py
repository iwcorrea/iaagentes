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

test_agent = Agent(
    role="Test Generator",
    goal="Generar tests unitarios con pytest para el backend generado.",
    backstory="""
Sos un ingeniero de testing experto en pytest.
Reglas:
- Analizá el código del backend y generá tests unitarios para cada endpoint.
- Usá el formato ruta:::código para entregar los archivos de test.
- Cubrí casos de éxito, error y autenticación.
- El archivo de test debe llamarse tests/test_api.py.
- Usá TestClient de FastAPI y pytest.
- NO añadas explicaciones ni markdown.
""",
    verbose=False,
    allow_delegation=False,
    llm=get_llm(),
    tools=[]
)