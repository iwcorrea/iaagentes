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

# ─── DASHBOARD ───
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

@app.post("/v1/chat/completions")
def chat_completions(
    request: ChatRequest,
    project_id: Optional[str] = Query(None),
    scope: Optional[str] = Query("all"),
    mode: Optional[str] = Query("full"),
    turbo: Optional[bool] = Query(False)
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

# ─── VALIDACIÓN DE PROMPT (SIN GENERAR) ───
@app.post("/api/validate-prompt")
def validate_prompt(data: dict):
    prompt = data.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt requerido")
    from core.prompt_integrity import PromptIntegrity
    validator = PromptIntegrity()
    validation = validator.validate(prompt)
    return {
        "valid": validation["valid"],
        "warnings": validation["warnings"],
        "suggestions": validation["suggestions"],
        "detected_types": validation["detected_types"],
        "improved_prompt": validator.build_improved_prompt(prompt) if not validation["valid"] else prompt
    }

# ─── ASISTENTE GUIADO ───
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

# ─── CONFIGURACIÓN ───
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

# ─── PROYECTOS ───
@app.get("/projects")
def list_projects():
    project_ids = project_manager.list_projects()
    projects = []
    for pid in project_ids:
        proj_path = project_manager.get_project_path(pid)
        name = pid
        if proj_path:
            meta_file = proj_path / "project.json"
            if meta_file.exists():
                try:
                    meta = json_module.loads(meta_file.read_text(encoding='utf-8'))
                    if "name" in meta:
                        name = meta["name"]
                except:
                    pass
        projects.append({"id": pid, "name": name})
    return {"projects": projects}

@app.get("/projects/{project_id}/files")
def list_project_files(project_id: str):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    files = [str(f.relative_to(project_path)) for f in project_path.rglob("*") if f.is_file()]
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
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": "Timeout instalando dependencias.", "execution_type": "desconocido"}

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

@app.get("/projects/{project_id}/audit")
def audit_project(project_id: str):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    from core.project_auditor import ProjectAuditor
    auditor = ProjectAuditor(str(project_path))
    issues = auditor.audit()
    return {"project_id": project_id, "issues": issues, "status": "ok" if not issues else "attention"}

# ─── MEJORAS ───
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

# ─── AGENTES ───
@app.get("/api/agents")
def get_agents_info():
    from core.agent_scanner import ComponentScanner
    from core.agent_status import get_status
    scanner = ComponentScanner()
    data = scanner.get_full_data()
    live = get_status()
    for team in data.get("teams", []):
        for agent in team.get("agents", []):
            if agent["name"] in live:
                agent["status"] = live[agent["name"]]["status"]
                agent["emoji"] = live[agent["name"]]["emoji"]
    return data

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