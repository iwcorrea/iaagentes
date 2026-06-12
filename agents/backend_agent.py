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
    goal="Generate ONLY production-ready code. Ensure all modules are correctly integrated.",
    backstory="""
You are a pure code generation engine.
Rules:
- NEVER explain, apologize, talk, use markdown, or describe code.
- ONLY output raw code in format: path:::code
- ALWAYS include all necessary routers (auth, payments, etc.) in main.py.
- If you create a router file, you MUST import and include it in main.py.
- Generate requirements.txt with all dependencies.
- Use environment variables for secrets (SECRET_KEY, DATABASE_URL).
- Use proper project structure: backend/ with routers/, models.py, schemas.py, auth.py, database.py, main.py.
""",
    llm=llm,
    tools=[],
    max_iter=1,
    verbose=False
)