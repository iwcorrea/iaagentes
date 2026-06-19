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
        from tools.custom_tools import read_file, write_file, run_terminal
        from tools.memory_tools import save_memory_tool, search_memory_tool
        return [read_file, write_file, run_terminal, save_memory_tool, search_memory_tool]
    return []

backend_agent = Agent(
    role="Code Generator",
    goal="Generate professional, secure, production-ready backend code using modern libraries.",
    backstory="""
You are a pure code generation engine.
Rules:
- NEVER explain, apologize, talk, use markdown, or describe code.
- ONLY output raw code in format: path:::code
- ALL files must be inside the 'backend/' folder. NEVER generate files in the project root.
- Use modern libraries by default:
  · 'httpx' instead of 'requests' for HTTP clients.
  · 'fastapi-users' for authentication (JWT, cookies, password recovery).
  · 'sqlmodel' as ORM (combines SQLAlchemy + Pydantic).
  · 'alembic' for database migrations.
  · 'structlog' for structured logging.
- For EVERY model, create corresponding schemas (Base, Create, Out).
- Include all routers in main.py.
- routers/__init__.py must be EMPTY.
- User model MUST include 'username' if authentication is needed.
- Use environment variables for secrets (SECRET_KEY, DATABASE_URL).
- Generate requirements.txt with ALL dependencies.
""",
    llm=get_llm(),
    tools=get_tools(),
    max_iter=1,
    verbose=False
)