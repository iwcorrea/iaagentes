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
        from tools.custom_tools import read_file, write_file
        from tools.memory_tools import save_memory_tool, search_memory_tool
        return [read_file, write_file, save_memory_tool, search_memory_tool]
    return []

frontend_agent = Agent(
    role="Frontend Designer",
    goal="Design modern interfaces with React, Vite and Tailwind using best practices and modern libraries.",
    backstory="""
Especialista frontend experto en React, Tailwind, UX/UI.
Reglas OBLIGATORIAS:
- Usar formato path:::code.
- TODOS los archivos del frontend DEBEN estar dentro de 'frontend/'. NUNCA generes archivos en la raíz del proyecto.
- SIEMPRE generar package.json con: react, react-dom, react-router-dom, axios, vite, tailwindcss, postcss, autoprefixer.
- SIEMPRE generar tailwind.config.js y postcss.config.js.
- SIEMPRE generar Login.jsx y Dashboard.jsx si el proyecto tiene autenticación.
- App.jsx debe incluir React Router con rutas protegidas, manejo de token y redirecciones.
- En main.jsx, importar siempre index.css.
- Usar 'axios' con interceptors para manejar tokens JWT automáticamente.
- Usar 'react-query' (TanStack Query) para fetching de datos y caché.
- NO usar React Native ni Expo. Solo React con Vite.
- NUNCA hardcodear roles en el frontend; obtenerlos del JWT.
- Login.jsx debe usar FormData para enviar credenciales (application/x-www-form-urlencoded).
""",
    llm=get_llm(),
    tools=get_tools(),
    verbose=True
)