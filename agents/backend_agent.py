import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from tools.custom_tools import read_file, write_file, run_terminal
from tools.memory_tools import save_memory_tool, search_memory_tool

load_dotenv()

llm = LLM(
    model="gratuito-fallback",
    api_key="no-necesita-key-real",
    base_url="http://localhost:4000/v1",
    api_base="http://localhost:4000/v1",
    stop=[]
)

backend_agent = Agent(
    role="Code Generator",
    goal="Generar código backend completo, seguro y listo para producción. Garantizar que main.py incluya TODOS los routers creados.",
    backstory="""
You are a pure code generation engine.
Rules:
- NEVER explain, apologize, talk, use markdown, or describe code.
- ONLY output raw code in format: path:::code
- ALL files must be inside the 'backend/' folder. NEVER generate files in the project root.
- If you create a router file (e.g., routers/auth.py, routers/payments.py), you MUST import it and add app.include_router(...) in main.py.
- main.py must include all existing routers.
- ALWAYS define schemas used by routers in schemas.py (Token, UserCreate, PaymentCreate, etc.).
- NEVER import schemas that don't exist. If you need a schema, define it first.
- PROTECT admin-only endpoints with Depends(auth.check_admin_role).
- Use environment variables for secrets (SECRET_KEY, DATABASE_URL).
- Generate requirements.txt with all dependencies.
""",
    llm=llm,
    tools=[],
    max_iter=1,
    verbose=False
)