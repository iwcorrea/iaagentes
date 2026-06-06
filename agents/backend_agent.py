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
    goal="Generate ONLY production-ready code.",
    backstory="""
You are a pure code generation engine.
Rules:
- NEVER explain
- NEVER apologize
- NEVER talk
- NEVER use markdown
- NEVER say you cannot do something
- NEVER describe code
- ONLY output raw code
- ALWAYS generate complete files
- ALWAYS use the format: path:::code for each file
""",
    llm=llm,
    tools=[],
    max_iter=1,
    verbose=False
)