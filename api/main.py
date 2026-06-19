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
from core.guided_builder import GuidedBuilder
from core.prompt_guard import validate_prompt

from api.routers import projects_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router.router)

project_manager = ProjectManager()
improvement_queue = ImprovementQueue()
config_assistant = ConfigAssistant()
guided_builder = GuidedBuilder()

SETTINGS_PATH = Path("settings.json")

def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        default_settings = {
            "models": {"primary": "gratuito-fallback", "temperature": 0.0, "max_tokens": 4096},
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
        "data": [{"id": "crewai-system", "object": "model", "created": 1234567890, "owned_by": "local"}]
    }

@app.get("/api/progress")
def get_progress_only():
    from core.agent_status import get_progress
    return {"progress": get_progress()}

@app.post("/v1/chat/completions")
def chat_completions(
    request: ChatRequest,
    project_id: Optional[str] = Query(None),
    scope: Optional[str] = Query("all"),
    mode: Optional[str] = Query("full"),
    turbo: Optional[bool] = Query(False),
    brain_model: Optional[str] = Query("local-coder")
):
    try:
        user_prompt = request.messages[-1].content
        intent = detect_intent(user_prompt)

        model_map = {
            "local-coder": "local-coder",
            "cloud-coder": "cloud-coder",
            "hibrido-coder": "hibrido-coder"
        }
        actual_model = model_map.get(brain_model, "local-coder")
        os.environ["CURRENT_BRAIN_MODEL"] = actual_model

        from core.agent_cache import clear_cache
        clear_cache()

        for mod in list(sys.modules.keys()):
            if mod.startswith("agents.") or mod == "core.meta_agent":
                del sys.modules[mod]

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
                mode=mode,
                turbo=turbo
            )

        final_text += f"\n\n🔹 Proyecto ID: {final_project_id}"
        print("FINAL TEXT:", repr(final_text[:300]))

        return {
            "id": "chatcmpl-local",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "crewai-system",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": final_text}, "finish_reason": "stop"}]
        }
    except Exception as e:
        return {
            "id": "chatcmpl-error",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": f"❌ Error del servidor:\n\n{str(e)}"}, "finish_reason": "stop"}]
        }

@app.post("/api/validate-prompt")
def validate_prompt_endpoint(data: dict):
    prompt = data.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt requerido")
    validation = validate_prompt(prompt)
    return validation

@app.get("/api/guided-templates")
def get_guided_templates():
    return {"templates": guided_builder.get_templates()}

@app.get("/api/guided-questions/{template_id}")
def get_guided_questions(template_id: str):
    questions = guided_builder.get_questions(template_id)
    if not questions:
        raise HTTPException(status_code=404, detail="Tipo de proyecto no encontrado")
    return {"questions": questions}

@app.post("/api/guided-preview")
def preview_guided_project(data: dict):
    template_id = data.get("template_id")
    answers = data.get("answers", {})
    if not template_id:
        raise HTTPException(status_code=400, detail="template_id requerido")
    prompt = guided_builder.preview_prompt(template_id, answers)
    return {"prompt": prompt}

@app.post("/api/create-guided-project")
def create_guided_project(data: dict):
    template_id = data.get("template_id")
    answers = data.get("answers", {})
    if not template_id:
        raise HTTPException(status_code=400, detail="template_id requerido")
    result = guided_builder.validate_and_build(template_id, answers)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    project_path = project_manager.create_project()
    final_project_id = project_path.name
    orchestrator = AutonomousArchitectOrchestrator(workspace_path=str(project_path))
    orchestrator.orchestrate_project(result["prompt"])
    return {
        "project_id": final_project_id,
        "prompt": result["prompt"],
        "files_expected": result["files_expected"],
        "message": "Proyecto creado exitosamente"
    }

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
    return {"status": "ok", "message": "Configuración guardada."}

@app.get("/system/dependency-cache-stats")
def dependency_cache_stats():
    from core.dependency_cache import DependencyCache
    cache = DependencyCache()
    return cache.stats()

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

@app.get("/api/agents")
def get_agents_info():
    from core.agent_scanner import ComponentScanner
    from core.agent_status import get_status, get_progress
    scanner = ComponentScanner()
    data = scanner.get_full_data()
    live = get_status()
    for team in data.get("teams", []):
        for agent in team.get("agents", []):
            if agent["name"] in live:
                agent["status"] = live[agent["name"]]["status"]
                agent["emoji"] = live[agent["name"]]["emoji"]
                agent["current_task"] = live[agent["name"]].get("current_task", "")
    return {"teams": data["teams"], "tools": data["tools"], "core_modules": data["core_modules"], "progress": get_progress()}

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