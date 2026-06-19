import os
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv()

current_model = os.getenv("CURRENT_BRAIN_MODEL", "local-coder")

llm = LLM(
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

Example: if the issue is "Routers not integrated in main.py", output:
backend/main.py:::from fastapi import FastAPI
from .routers import auth, wallets
app = FastAPI()
app.include_router(auth.router)
app.include_router(wallets.router)
""",
    verbose=False,
    allow_delegation=False,
    llm=llm,
    tools=[]  # sin herramientas para evitar errores de function calling
)