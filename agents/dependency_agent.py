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

# Caché simple para dependencias
_dep_cache = {}

def get_cached_dependencies(imports: list) -> dict:
    """Retorna dependencias cacheadas para los imports dados."""
    result = {}
    for imp in imports:
        if imp in _dep_cache:
            result[imp] = _dep_cache[imp]
    return result

def add_to_cache(imports_map: dict):
    """Agrega mapeos al caché."""
    _dep_cache.update(imports_map)

dependency_agent = Agent(
    role="Dependency Manager",
    goal="Generate or fix requirements.txt and package.json based on the generated code. Use cache when possible.",
    backstory="""
You are an expert in Python and JavaScript dependencies.
Rules:
- Analyze the provided code and generate a complete requirements.txt for Python and package.json for Node.js.
- If requirements.txt or package.json are already present but incomplete, fix them.
- ONLY return the corrected files in path:::code format.
- NEVER add explanations or markdown.
- If you already know a dependency for an import (cache hit), reuse it without calling the LLM.
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)