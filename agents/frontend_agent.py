import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from tools.custom_tools import read_file, write_file
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

Ejemplo de formato de salida:
frontend/src/components/Login.jsx:::import { useState } from 'react'
import axios from 'axios'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)
      const res = await axios.post('http://localhost:8000/auth/token', formData)
      onLogin(res.data.access_token)
    } catch (err) {
      setError('Credenciales incorrectas')
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" value={username} onChange={e => setUsername(e.target.value)} />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button type="submit">Iniciar sesión</button>
      {error && <p>{error}</p>}
    </form>
  )
}
""",
    llm=llm,
    tools=[read_file, write_file, save_memory_tool, search_memory_tool],
    verbose=True
)