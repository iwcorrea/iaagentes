import os
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv()

llm = LLM(
    model="gratuito-fallback",
    api_key="no-necesita-key-real",
    base_url="http://localhost:4000/v1",
    api_base="http://localhost:4000/v1",
    stop=[]
)

dependency_agent = Agent(
    role="Dependency Manager",
    goal="Generate or fix requirements.txt and package.json based on the generated code.",
    backstory="""
You are an expert in Python and JavaScript dependencies.
Rules:
- Analyze the provided code and generate a complete requirements.txt for Python and package.json for Node.js.
- If requirements.txt or package.json are already present but incomplete, fix them.
- ONLY return the corrected files in path:::code format.
- NEVER add explanations or markdown.
""",
    verbose=False,
    allow_delegation=False,
    llm=llm
)