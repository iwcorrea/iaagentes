import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # Elimina warning en Windows

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import tempfile
import os
import subprocess
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

app.mount("/static", StaticFiles(directory="frontend"), name="static")

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

        project_path = project_manager.create_project(project_id)
        final_project_id = project_path.name

        if intent == "create_file":
            final_text = generate_file(user_prompt, project_path=project_path)  # ← CORREGIDO
        elif intent == "terminal":
            final_text = "Terminal execution not implemented yet."
        else:
            orchestrator = AutonomousArchitectOrchestrator(workspace_path=str(project_path))
            final_text = orchestrator.orchestrate_project(user_prompt)

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

# Graph export (sin cambios)
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

# Auto-mejora (sin cambios)
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
    return {"proposals": proposals, "count": len(proposals)}

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
        project_path = project_manager.base / project_id / "backend"
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Proyecto {project_id} sin backend")
        memory = ArchitectureMemory(root_path=str(project_path))
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

# Métricas de calidad
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

# Listar proyectos
@app.get("/projects")
def list_projects():
    return {"projects": project_manager.list_projects()}

# Panel de supervisión
@app.get("/improvements")
def improvements_panel():
    return FileResponse("frontend/improvements.html")