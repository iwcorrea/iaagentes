import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Query, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response, JSONResponse, FileResponse
from pydantic import BaseModel
import tempfile
import os
import subprocess
import sys
import json as json_module
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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ya no montamos la carpeta frontend estática

project_manager = ProjectManager()
improvement_queue = ImprovementQueue()

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
def chat_completions(request: ChatRequest, project_id: Optional[str] = Query(None)):
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
            final_text = orchestrator.orchestrate_project(user_prompt, is_modification=is_modification)

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
    """
    Devuelve la lista de agentes, sus tools, y los módulos core del ecosistema.
    """
    agents = [
        {
            "name": "Director IA",
            "role": "Arquitecto de Software",
            "emoji": "🧠",
            "status": "idle",
            "tools": ["Read File", "Run Terminal", "save_memory", "search_memory"],
            "description": "Planifica la arquitectura del proyecto y coordina a los demás agentes."
        },
        {
            "name": "Code Generator",
            "role": "Desarrollador Backend",
            "emoji": "💻",
            "status": "idle",
            "tools": ["Write File", "Read File"],
            "description": "Genera código Python limpio y funcional siguiendo las mejores prácticas."
        },
        {
            "name": "Frontend Designer",
            "role": "Diseñador Frontend",
            "emoji": "🎨",
            "status": "idle",
            "tools": ["Write File", "Read File"],
            "description": "Crea interfaces modernas con React y Tailwind CSS."
        },
        {
            "name": "QA Auditor",
            "role": "Ingeniero de Calidad",
            "emoji": "🔍",
            "status": "idle",
            "tools": ["Read File", "Run Terminal"],
            "description": "Revisa el código en busca de errores, vulnerabilidades y malas prácticas."
        },
        {
            "name": "Repair Agent",
            "role": "Ingeniero de Depuración",
            "emoji": "🔧",
            "status": "idle",
            "tools": [],
            "description": "Corrige bugs y problemas de código automáticamente."
        }
    ]
    
    tools = [
        {"name": "Read File", "description": "Lee el contenido de cualquier archivo del proyecto."},
        {"name": "Write File", "description": "Escribe o sobrescribe archivos con nuevo contenido."},
        {"name": "Run Terminal", "description": "Ejecuta comandos en la terminal del sistema."},
        {"name": "save_memory", "description": "Guarda información en la memoria vectorial del ecosistema."},
        {"name": "search_memory", "description": "Busca información semántica en la memoria vectorial."}
    ]
    
    core_modules = [
        {"name": "architect_orchestrator", "description": "Orquesta todo el flujo de generación y reparación."},
        {"name": "architecture_memory", "description": "Mantiene el grafo de dependencias del proyecto."},
        {"name": "executor", "description": "Ejecuta el proyecto generado y captura la salida."},
        {"name": "refactor_engine", "description": "Analiza y sugiere refactorizaciones estáticas."},
        {"name": "meta_agent", "description": "Genera propuestas de mejora automáticas."},
        {"name": "improvement_queue", "description": "Cola de mejoras pendientes, aprobadas y aplicadas."},
        {"name": "project_manager", "description": "Gestiona la creación y listado de proyectos."},
        {"name": "sandbox", "description": "Aplica cambios de código de forma segura con backup."}
    ]
    
    return {"agents": agents, "tools": tools, "core_modules": core_modules}

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