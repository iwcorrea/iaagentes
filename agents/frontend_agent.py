import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from tools.custom_tools import read_file, write_file
from tools.memory_tools import save_memory_tool, search_memory_tool

load_dotenv()

llm = LLM(
    model="gratuito-fallback",
    api_key="no-necesita-key-real",
    base_url="http://localhost:4000/v1",
    api_base="http://localhost:4000/v1",
    stop=[]
)

frontend_agent = Agent(
    role="Frontend Designer",
    goal="Diseñar interfaces modernas y responsive.",
    backstory="""
Especialista frontend experto en React y Tailwind.
Rules:
- Use format path:::code
- Never hardcode user roles ('admin', 'collector') in frontend logic. Roles must come from JWT payload.
- Use environment variables for API URLs (VITE_API_URL).
- Always match backend endpoint names exactly (check backend routers).
- Use proper error handling with try/catch, not alerts.
- Use HttpOnly cookies for token storage if possible, otherwise localStorage with caution.
""",
    llm=llm,
    tools=[read_file, write_file, save_memory_tool, search_memory_tool],
    verbose=True
)