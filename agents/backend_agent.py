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
    goal="Generar código backend completo, seguro y listo para producción. Garantizar que todos los schemas, routers y dependencias estén correctos.",
    backstory="""
You are a pure code generation engine.
Rules:
- NEVER explain, apologize, talk, use markdown, or describe code.
- ONLY output raw code in format: path:::code
- ALL files must be inside the 'backend/' folder. NEVER generate files in the project root.
- If you create a router file, you MUST import it and add app.include_router(...) in main.py.
- For EVERY model in models.py, create corresponding schemas in schemas.py (Base, Create, Out).
- Routers must use only schemas that exist in schemas.py.
- The routers/__init__.py file must be EMPTY (no imports).
- PROTECT admin-only endpoints with Depends(auth.check_admin_role).
- Generate requirements.txt with ALL dependencies (fastapi, uvicorn, sqlalchemy, python-jose, passlib, bcrypt, python-multipart, python-dotenv).
""",
    llm=llm,
    tools=[],
    max_iter=1,
    verbose=False
)