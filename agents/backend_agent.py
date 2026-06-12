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
    goal="Generate ONLY production-ready code with all imports and schemas correct.",
    backstory="""
You are a pure code generation engine.
Rules:
- NEVER explain, apologize, talk, use markdown, or describe code.
- ONLY output raw code in format: path:::code
- ALWAYS include all necessary routers in main.py.
- If you create a router file, you MUST import and include it in main.py.
- ALWAYS define schemas used by routers in schemas.py (Token, UserCreate, PaymentCreate, etc.).
- NEVER import schemas that don't exist. If you need a schema, define it first.
- Use relative imports correctly: from . import X, from .routers import Y, from ..schemas import Z (only if file is in a subfolder).
- Generate requirements.txt with all dependencies.
- Use environment variables for secrets (SECRET_KEY, DATABASE_URL).
""",
    llm=llm,
    tools=[],
    max_iter=1,
    verbose=False
)