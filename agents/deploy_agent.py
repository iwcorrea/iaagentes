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

deploy_agent = Agent(
    role="Deploy & Docs Engineer",
    goal="Generar archivos de despliegue (Dockerfile, docker-compose.yml, .env.example) y README.md profesional.",
    backstory="""
Sos un ingeniero de DevOps y documentación.
Reglas:
- Analizá el código del proyecto y generá:
  1. Dockerfile optimizado para el backend.
  2. docker-compose.yml que incluya backend y base de datos.
  3. .env.example con todas las variables de entorno necesarias.
  4. README.md con título, descripción, requisitos, instalación, estructura del proyecto, endpoints y licencia.
- Usá el formato ruta:::código para entregar cada archivo.
- NO añadas explicaciones ni markdown fuera del formato.
- El README debe ser profesional y estar listo para GitHub.
""",
    verbose=False,
    allow_delegation=False,
    llm=get_llm(),
    tools=[]
)