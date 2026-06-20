import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import shutil
from datetime import datetime
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECTS_ROOT = Path("projects")
PROJECTS_ROOT.mkdir(exist_ok=True)

class ProjectCreate(BaseModel):
    prompt: str

class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: str
    path: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: ChatMessage

# ============ ENDPOINTS ============

@app.get("/")
def root():
    return {"status": "ok", "message": "AI Ecosystem API running"}

@app.get("/api/projects", response_model=List[ProjectResponse])
def list_projects():
    projects = []
    for item in PROJECTS_ROOT.iterdir():
        if item.is_dir():
            meta_path = item / "project.json"
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        projects.append(ProjectResponse(
                            id=meta.get("id", item.name),
                            name=meta.get("name", item.name),
                            created_at=meta.get("created_at", datetime.now().isoformat()),
                            path=str(item)
                        ))
                except:
                    projects.append(ProjectResponse(
                        id=item.name,
                        name=item.name,
                        created_at=datetime.now().isoformat(),
                        path=str(item)
                    ))
            else:
                projects.append(ProjectResponse(
                    id=item.name,
                    name=item.name,
                    created_at=datetime.now().isoformat(),
                    path=str(item)
                ))
    return projects

@app.post("/api/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate):
    project_id = str(uuid.uuid4())[:8]
    project_name = project.prompt[:30].replace(" ", "_").replace("/", "_")
    project_path = PROJECTS_ROOT / project_name
    project_path.mkdir(exist_ok=True)
    
    meta = {
        "id": project_id,
        "name": project_name,
        "prompt": project.prompt,
        "created_at": datetime.now().isoformat(),
        "path": str(project_path)
    }
    with open(project_path / "project.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    # Crear estructura básica del proyecto
    (project_path / "backend").mkdir(exist_ok=True)
    (project_path / "frontend").mkdir(exist_ok=True)
    
    return ProjectResponse(
        id=project_id,
        name=project_name,
        created_at=meta["created_at"],
        path=str(project_path)
    )

@app.get("/api/projects/{project_id}/chat", response_model=List[ChatMessage])
def get_chat_history(project_id: str):
    # Buscar proyecto por ID o nombre
    for item in PROJECTS_ROOT.iterdir():
        if item.is_dir():
            meta_path = item / "project.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    if meta.get("id") == project_id or item.name == project_id:
                        chat_path = item / "chat.json"
                        if chat_path.exists():
                            with open(chat_path, "r", encoding="utf-8") as f:
                                return json.load(f)
                        return []
    raise HTTPException(status_code=404, detail="Proyecto no encontrado")

@app.post("/api/projects/{project_id}/chat", response_model=ChatResponse)
def send_message(project_id: str, request: ChatRequest):
    # Buscar proyecto
    project_path = None
    for item in PROJECTS_ROOT.iterdir():
        if item.is_dir():
            meta_path = item / "project.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    if meta.get("id") == project_id or item.name == project_id:
                        project_path = item
                        break
    
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    chat_path = project_path / "chat.json"
    messages = []
    if chat_path.exists():
        with open(chat_path, "r", encoding="utf-8") as f:
            messages = json.load(f)
    
    messages.append({"role": "user", "content": request.message})
    
    # Simular respuesta (aquí iría la lógica real de agentes)
    response_content = f"✅ Recibido: '{request.message}'. Procesando solicitud para el proyecto {project_path.name}."
    messages.append({"role": "assistant", "content": response_content})
    
    with open(chat_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
    
    return ChatResponse(message=ChatMessage(role="assistant", content=response_content))

# ============ ENDPOINTS DE ESTADO (mock) ============

@app.get("/api/agents")
def get_agents():
    return {
        "teams": [
            {
                "name": "Equipo Principal",
                "agents": [
                    {"name": "Director", "status": "idle", "emoji": "🧠", "current_task": "Esperando instrucciones"},
                    {"name": "Backend", "status": "idle", "emoji": "⚙️", "current_task": "Esperando"},
                    {"name": "Frontend", "status": "idle", "emoji": "🎨", "current_task": "Esperando"},
                ]
            }
        ],
        "tools": ["file_writer", "file_reader", "terminal"],
        "core_modules": ["architect_orchestrator", "project_manager"],
        "progress": 0
    }

@app.get("/api/progress")
def get_progress():
    return {"progress": 0}

@app.get("/api/settings")
def get_settings():
    return {
        "models": {"primary": "local-coder", "temperature": 0.0, "max_tokens": 4096},
        "agents": {},
        "teams": [],
        "available_agents": ["Director", "Backend", "Frontend"],
        "available_tools": ["file_writer", "file_reader", "terminal"]
    }

@app.put("/api/settings")
def update_settings(settings: dict):
    return {"status": "ok", "message": "Configuración guardada (mock)"}

# ============ ENDPOINT DE CHAT PRINCIPAL ============

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]

@app.post("/v1/chat/completions")
def chat_completions(request: ChatCompletionRequest, project_id: Optional[str] = Query(None)):
    try:
        user_prompt = request.messages[-1].content if request.messages else ""
        
        # Si no hay project_id, crear uno automáticamente
        if not project_id:
            project_id = str(uuid.uuid4())[:8]
            project_name = user_prompt[:20].replace(" ", "_")
            project_path = PROJECTS_ROOT / project_name
            project_path.mkdir(exist_ok=True)
            meta = {
                "id": project_id,
                "name": project_name,
                "prompt": user_prompt,
                "created_at": datetime.now().isoformat(),
                "path": str(project_path)
            }
            with open(project_path / "project.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            (project_path / "backend").mkdir(exist_ok=True)
            (project_path / "frontend").mkdir(exist_ok=True)
        
        # Simular respuesta de los agentes
        response = f"""📋 **Proyecto procesado**

✅ ID: {project_id}
📁 Carpeta: {PROJECTS_ROOT / project_id}

**Prompt recibido:**
{user_prompt}

**Acciones realizadas:**
- Estructura de proyecto creada
- Backend y frontend inicializados
- Los agentes están listos para trabajar

💡 Puedes continuar conversando para modificar o expandir el proyecto.
"""
        
        # Guardar en el chat del proyecto
        for item in PROJECTS_ROOT.iterdir():
            if item.is_dir():
                meta_path = item / "project.json"
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        if meta.get("id") == project_id or item.name == project_id:
                            chat_path = item / "chat.json"
                            messages = []
                            if chat_path.exists():
                                with open(chat_path, "r", encoding="utf-8") as f:
                                    messages = json.load(f)
                            messages.append({"role": "user", "content": user_prompt})
                            messages.append({"role": "assistant", "content": response})
                            with open(chat_path, "w", encoding="utf-8") as f:
                                json.dump(messages, f, indent=2, ensure_ascii=False)
                            break
        
        return {
            "id": "chatcmpl-local",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "crewai-system",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response},
                "finish_reason": "stop"
            }]
        }
    except Exception as e:
        return {
            "id": "chatcmpl-error",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": f"❌ Error: {str(e)}"},
                "finish_reason": "stop"
            }]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)