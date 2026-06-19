import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from tools.custom_tools import read_file, write_file, run_terminal
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

supports_tools = current_model in ("cloud-coder", "hibrido-coder")
agent_tools = [read_file, write_file, run_terminal, save_memory_tool, search_memory_tool] if supports_tools else []

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
    llm=llm,
    tools=agent_tools,
    max_iter=1,
    verbose=False
)