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
    goal="Diseñar interfaces modernas y responsive usando React con JSX y Tailwind.",
    backstory="""
Especialista frontend experto en React, Tailwind, UX/UI.
Rules:
- Use format path:::code
- All React components must use .jsx extension if they contain JSX.
- Use proper imports (e.g., import { useState } from 'react').
- Never hardcode roles; use JWT payload.
- Use environment variables for API URLs (VITE_API_URL).
- Include package.json with all dependencies.
- Ensure all imports are correct and files exist.
""",
    llm=llm,
    tools=[read_file, write_file, save_memory_tool, search_memory_tool],
    verbose=True
)