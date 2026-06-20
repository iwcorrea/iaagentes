from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from datetime import datetime

router = APIRouter()

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

PROJECTS_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "projects")
os.makedirs(PROJECTS_ROOT, exist_ok=True)

@router.get("/", response_model=List[ProjectResponse])
async def list_projects():
    projects = []
    if os.path.exists(PROJECTS_ROOT):
        for item in os.listdir(PROJECTS_ROOT):
            project_path = os.path.join(PROJECTS_ROOT, item)
            if os.path.isdir(project_path):
                meta_path = os.path.join(project_path, "project.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            projects.append(ProjectResponse(
                                id=meta.get("id", item),
                                name=meta.get("name", item),
                                created_at=meta.get("created_at", datetime.now().isoformat()),
                                path=project_path
                            ))
                    except:
                        projects.append(ProjectResponse(
                            id=item,
                            name=item,
                            created_at=datetime.now().isoformat(),
                            path=project_path
                        ))
                else:
                    projects.append(ProjectResponse(
                        id=item,
                        name=item,
                        created_at=datetime.now().isoformat(),
                        path=project_path
                    ))
    return projects

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    import uuid
    project_id = str(uuid.uuid4())[:8]
    project_name = project.prompt[:30].replace(" ", "_")
    project_path = os.path.join(PROJECTS_ROOT, project_name)
    os.makedirs(project_path, exist_ok=True)
    meta = {
        "id": project_id,
        "name": project_name,
        "prompt": project.prompt,
        "created_at": datetime.now().isoformat(),
        "path": project_path
    }
    with open(os.path.join(project_path, "project.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    return ProjectResponse(
        id=project_id,
        name=project_name,
        created_at=meta["created_at"],
        path=project_path
    )

@router.get("/{project_id}/chat", response_model=List[ChatMessage])
async def get_chat_history(project_id: str):
    project_path = None
    if os.path.exists(PROJECTS_ROOT):
        for item in os.listdir(PROJECTS_ROOT):
            meta_path = os.path.join(PROJECTS_ROOT, item, "project.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    if meta.get("id") == project_id:
                        project_path = os.path.join(PROJECTS_ROOT, item)
                        break
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    chat_path = os.path.join(project_path, "chat.json")
    if os.path.exists(chat_path):
        with open(chat_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@router.post("/{project_id}/chat", response_model=ChatResponse)
async def send_message(project_id: str, request: ChatRequest):
    project_path = None
    if os.path.exists(PROJECTS_ROOT):
        for item in os.listdir(PROJECTS_ROOT):
            meta_path = os.path.join(PROJECTS_ROOT, item, "project.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    if meta.get("id") == project_id:
                        project_path = os.path.join(PROJECTS_ROOT, item)
                        break
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    chat_path = os.path.join(project_path, "chat.json")
    messages = []
    if os.path.exists(chat_path):
        with open(chat_path, "r", encoding="utf-8") as f:
            messages = json.load(f)
    messages.append({"role": "user", "content": request.message})
    assistant_response = f"Recibido: '{request.message}'. Los agentes están procesando tu solicitud."
    messages.append({"role": "assistant", "content": assistant_response})
    with open(chat_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
    return ChatResponse(message=ChatMessage(role="assistant", content=assistant_response))