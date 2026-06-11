import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Query, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import tempfile
import os
import subprocess
import sys
import json as json_module
import shutil
from typing import Optional
from pathlib import Path

from core.router import detect_intent
from core.file_generator import generate_file
from core.architect_orchestrator import AutonomousArchitectOrchestrator
from core.architecture_memory import ArchitectureMemory
from core.improvement_queue import ImprovementQueue
from core.meta_agent import MetaAgent
from core.sandbox import apply_improvement_safe
from core.project_manager import ProjectManager
from core.quality_metrics import analyze_quality
from core.config_assistant import ConfigAssistant

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

project_manager = ProjectManager()
improvement_queue = ImprovementQueue()
config_assistant = ConfigAssistant()

SETTINGS_PATH = Path("settings.json")

def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        default_settings = {
            "models": {
                "primary": "gratuito-fallback",
                "temperature": 0.0,
                "max_tokens": 4096
            },
            "agents": {},
            "teams": []
        }
        save_settings(default_settings)
        return default_settings
    try:
        return json_module.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
    except:
        return {}

def save_settings(settings: dict):
    backup_path = SETTINGS_PATH.with_suffix('.json.bak')
    if SETTINGS_PATH.exists():
        shutil.copy2(SETTINGS_PATH, backup_path)
    SETTINGS_PATH.write_text(json_module.dumps(settings, indent=2), encoding='utf-8')

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]

class ImprovementProposal(BaseModel):
    agent_name: str
    title: str
    description: str
    target_file: str
    suggested_code: Optional[str] = ""
    reason: Optional[str] = ""

# ─── CONFIGURACIÓN DEL SISTEMA ───
@app.get("/api/settings")
def get_settings():
    settings = load_settings()
    from core.agent_scanner import ComponentScanner
    scanner = ComponentScanner()
    settings["available_agents"] = scanner.scan_agents()
    settings["available_tools"] = scanner.scan_tools()
    return settings

@app.put("/api/settings")
def update_settings(settings: dict):
    current = load_settings()
    for section in ["models", "agents", "teams"]:
        if section in settings:
            current[section] = settings[section]
    save_settings(current)
    return {"status": "ok", "message": "Configuración guardada. Reinicia los agentes si es necesario."}

# ─── ASISTENTE DE CONFIGURACIÓN GUIADA ───
@app.get("/api/project-types")
def get_project_types():
    types = config_assistant.get_project_types()
    return {"types": types}

@app.get("/api/project-questions/{project_type}")
def get_project_questions(project_type: str):
    questions = config_assistant.get_questions(project_type)
    if not questions:
        raise HTTPException(status_code=404, detail="Tipo de proyecto no encontrado")
    return {"questions": questions}

@app.post("/api/create-guided-project")
def create_guided_project(data: dict):
    project_type = data.get("project_type")
    answers = data.get("answers", {})
    
    if not project_type:
        raise HTTPException(status_code=400, detail="Tipo de proyecto requerido")
    
    prompt = config_assistant.build_prompt(project_type, answers)
    project_path = project_manager.create_project()
    final_project_id = project_path.name
    
    orchestrator = AutonomousArchitectOrchestrator(workspace_path=str(project_path))
    orchestrator.orchestrate_project(prompt)
    
    return {
        "project_id": final_project_id,
        "prompt": prompt,
        "message": "Proyecto creado exitosamente"
    }

@app.get("/dashboard")
def dashboard():
    return {"message": "Usa el nuevo frontend React en nfrontend/frontend"}

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "crewai-system",
                "object": "model",
                "created": 1234567890,
                "owned_by": "local"
            }
        ]
    }

@app.post("/v1/chat/completions")
def chat_completions(
    request: ChatRequest,
    project_id: Optional[str] = Query(None),
    scope: Optional[str] = Query("all"),
    mode: Optional[str] = Query("full")
):
    try:
        user_prompt = request.messages[-1].content
        intent = detect_intent(user_prompt)

        is_modification = False
        if project_id:
            existing = project_manager.get_project_path(project_id)
            if existing:
                project_path = existing
                is_modification = True
                final_project_id = project_id
            else:
                project_path = project_manager.create_project(project_id)
                final_project_id = project_path.name
        else:
            project_path = project_manager.create_project(project_id)
            final_project_id = project_path.name

        if intent == "create_file":
            final_text = generate_file(user_prompt, project_path=project_path)
        elif intent == "terminal":
            final_text = "Terminal execution not implemented yet."
        else:
            orchestrator = AutonomousArchitectOrchestrator(workspace_path=str(project_path))
            final_text = orchestrator.orchestrate_project(
                user_prompt,
                is_modification=is_modification,
                scope=scope,
                mode=mode
            )

        final_text += f"\n\n🔹 Proyecto ID: {final_project_id}"
        print("FINAL TEXT:", repr(final_text[:300]))

        return {
            "id": "chatcmpl-local",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "crewai-system",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": final_text
                    },
                    "finish_reason": "stop"
                }
            ]
        }
    except Exception as e:
        return {
            "id": "chatcmpl-error",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "crewai-system",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"SERVER ERROR:\n\n{str(e)}"
                    },
                    "finish_reason": "stop"
                }
            ]
        }

# Graph export
@app.get("/graph/export")
def export_graph(format: str = Query("dot"), project_id: Optional[str] = Query(None)):
    if project_id is None:
        projects = project_manager.list_projects()
        if not projects:
            raise HTTPException(status_code=404, detail="No hay proyectos disponibles")
        project_id = projects[-1]
    project_path = project_manager.base / project_id / "backend"
    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Proyecto {project_id} no encontrado o sin backend")
    memory = ArchitectureMemory(root_path=str(project_path))
    memory.scan_project()
    dot_code = memory.export_graphviz()
    if format == "dot":
        return PlainTextResponse(content=dot_code, media_type="text/plain")
    elif format == "png":
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
                f.write(dot_code)
                dot_path = f.name
            png_path = dot_path.replace('.dot', '.png')
            result = subprocess.run(['dot', '-Tpng', dot_path, '-o', png_path], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise Exception(f"Error de Graphviz: {result.stderr}")
            with open(png_path, 'rb') as f:
                png_data = f.read()
            os.unlink(dot_path)
            os.unlink(png_path)
            return Response(content=png_data, media_type="image/png")
        except FileNotFoundError:
            raise HTTPException(status_code=503, detail="Graphviz no instalado.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al generar PNG: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Formato no soportado. Usa 'dot' o 'png'.")

# Auto-mejora
@app.post("/system/propose-improvement")
def propose_improvement(proposal: ImprovementProposal):
    proposal_id = improvement_queue.add_proposal(
        agent_name=proposal.agent_name,
        title=proposal.title,
        description=proposal.description,
        target_file=proposal.target_file,
        suggested_code=proposal.suggested_code,
        reason=proposal.reason
    )
    return {"status": "ok", "proposal_id": proposal_id}

@app.get("/system/improvements")
def list_improvements(status: str = Query("pending")):
    if status == "all":
        proposals = improvement_queue.list_all()
    elif status == "pending":
        proposals = improvement_queue.list_pending()
    else:
        proposals = [p for p in improvement_queue.list_all() if p["status"] == status]
    
    filtered = []
    for p in proposals:
        target_path = Path(p["target_file"])
        if target_path.exists():
            filtered.append(p)
    return {"proposals": filtered, "count": len(filtered)}

@app.post("/system/apply-improvement/{proposal_id}")
def apply_improvement(proposal_id: str, test_command: Optional[str] = None):
    proposal = improvement_queue.approve(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada o ya procesada")
    if not proposal.get("suggested_code"):
        improvement_queue.mark_applied(proposal_id, "Sin código automático")
        return {"status": "ok", "message": "Propuesta aprobada sin código."}
    success, msg = apply_improvement_safe(
        target_file=proposal["target_file"],
        new_code=proposal["suggested_code"],
        test_command=test_command
    )
    if success:
        improvement_queue.mark_applied(proposal_id, msg)
        return {"status": "ok", "message": msg}
    else:
        improvement_queue.mark_applied(proposal_id, f"FAILED: {msg}")
        raise HTTPException(status_code=400, detail=f"Mejora no aplicada: {msg}")

@app.post("/system/reject-improvement/{proposal_id}")
def reject_improvement(proposal_id: str):
    if improvement_queue.reject(proposal_id):
        return {"status": "ok", "message": "Propuesta rechazada"}
    raise HTTPException(status_code=404, detail="Propuesta no encontrada o ya procesada")

@app.post("/system/run-meta-agent")
def run_meta_agent(project_id: Optional[str] = Query(None)):
    try:
        projects = project_manager.list_projects()
        if not projects:
            raise HTTPException(status_code=404, detail="No hay proyectos")
        if project_id is None:
            project_id = projects[-1]
        project_path = project_manager.base / project_id
        backend_path = project_path / "backend"
        if not backend_path.exists():
            backend_path = project_path
        memory = ArchitectureMemory(root_path=str(backend_path))
        memory.scan_project()
        meta = MetaAgent(memory=memory, queue=improvement_queue)
        proposal_ids = meta.analyze_and_propose(project_root=".")
        return {
            "status": "ok",
            "message": f"MetaAgent generó {len(proposal_ids)} propuestas",
            "proposal_ids": proposal_ids,
            "project_id": project_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error MetaAgent: {str(e)}")

@app.get("/system/metrics")
def get_quality_metrics(project_id: Optional[str] = Query(None)):
    try:
        projects = project_manager.list_projects()
        if not projects:
            raise HTTPException(status_code=404, detail="No hay proyectos")
        if project_id is None:
            project_id = projects[-1]
        project_path = project_manager.base / project_id / "backend"
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Proyecto {project_id} sin backend")
        metrics = analyze_quality(str(project_path))
        return {"project_id": project_id, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo métricas: {str(e)}")

@app.get("/projects")
def list_projects():
    return {"projects": project_manager.list_projects()}

@app.get("/projects/{project_id}/files")
def list_project_files(project_id: str):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    files = []
    for f in project_path.rglob("*"):
        if f.is_file():
            files.append(str(f.relative_to(project_path)))
    return {"project_id": project_id, "files": sorted(files)}

@app.get("/projects/{project_id}/file")
def get_project_file(project_id: str, path: str = Query(...)):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    file_path = project_path / path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return {"filename": path, "content": file_path.read_text(encoding='utf-8')}

@app.put("/projects/{project_id}/file")
def update_project_file(project_id: str, path: str = Query(...), content: str = Body(..., embed=True)):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    file_path = project_path / path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    file_path.write_text(content, encoding='utf-8')
    return {"status": "ok", "message": "Archivo actualizado"}

@app.post("/projects/{project_id}/execute")
def execute_project_endpoint(project_id: str):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    req_file = project_path / "backend" / "requirements.txt"
    if not req_file.exists():
        req_file = project_path / "requirements.txt"
    
    if req_file.exists():
        try:
            install_result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                capture_output=True, text=True, timeout=60
            )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Timeout instalando dependencias.",
                "execution_type": "desconocido"
            }

    from core.executor import ProjectExecutor
    executor = ProjectExecutor(str(project_path))
    result = executor.execute_project()
    return {
        "success": result.get("success", False),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "execution_type": result.get("execution_type", "desconocido")
    }

@app.get("/projects/{project_id}/chat")
def get_project_chat(project_id: str):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    chat_path = project_path / "chat.json"
    if chat_path.exists():
        return json_module.loads(chat_path.read_text(encoding='utf-8'))
    return {"messages": []}

@app.post("/projects/{project_id}/chat")
async def save_project_chat(project_id: str, request: Request):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    chat_path = project_path / "chat.json"
    body = await request.json()
    chat_path.write_text(json_module.dumps(body, indent=2), encoding='utf-8')
    return {"status": "ok"}

@app.put("/projects/{project_id}/name")
def update_project_name(project_id: str, name: str = Body(..., embed=True)):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    meta_path = project_path / "project.json"
    meta = {}
    if meta_path.exists():
        meta = json_module.loads(meta_path.read_text(encoding='utf-8'))
    meta["name"] = name
    meta_path.write_text(json_module.dumps(meta, indent=2), encoding='utf-8')
    return {"status": "ok", "name": name}

@app.get("/projects/{project_id}/name")
def get_project_name(project_id: str):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    meta_path = project_path / "project.json"
    if meta_path.exists():
        meta = json_module.loads(meta_path.read_text(encoding='utf-8'))
        return {"name": meta.get("name", project_id)}
    return {"name": project_id}

@app.get("/api/agents")
def get_agents_info():
    from core.agent_scanner import ComponentScanner
    scanner = ComponentScanner()
    return scanner.get_full_data()

@app.post("/system/cleanup-improvements")
def cleanup_improvements():
    proposals = improvement_queue.list_all()
    removed = 0
    for p in proposals:
        target_path = Path(p["target_file"])
        if not target_path.exists():
            improvement_queue.reject(p["id"])
            removed += 1
    return {"removed": removed}

@app.get("/improvements")
def improvements_panel():
    return {"message": "Usa el nuevo panel React"}