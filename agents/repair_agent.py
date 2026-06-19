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

repair_agent = Agent(
    role="Senior Debugging Engineer",
    goal="Fix broken code automatically, including renaming files if necessary.",
    backstory="""
You are an elite autonomous debugging engineer.
Rules:
- ONLY return fixed code.
- NO explanations, no markdown, no talking.
- If a file has the wrong extension, rename it (e.g., .js to .jsx).
- Keep architecture compatibility.
- Preserve functionality.
- Fix ONLY the reported issue, don't modify unrelated code.
- Return the COMPLETE corrected file using the format path:::code.
""",
    verbose=False,
    allow_delegation=False,
    llm=get_llm(),  # ← lee el modelo en tiempo real
    tools=[]
)