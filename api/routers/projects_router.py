from fastapi import APIRouter, Query, HTTPException, Request, Body
import subprocess
import sys
import json as json_module
from pathlib import Path
from typing import Optional

router = APIRouter()

# Importamos project_manager desde el contexto de la app
from core.project_manager import ProjectManager
from core.executor import ProjectExecutor

project_manager = ProjectManager()

@router.get("/projects")
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

@router.get("/projects/{project_id}/files")
def list_project_files(project_id: str):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    files = [str(f.relative_to(project_path)) for f in project_path.rglob("*") if f.is_file()]
    return {"project_id": project_id, "files": sorted(files)}

@router.get("/projects/{project_id}/file")
def get_project_file(project_id: str, path: str = Query(...)):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    file_path = project_path / path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return {"filename": path, "content": file_path.read_text(encoding='utf-8')}

@router.put("/projects/{project_id}/file")
def update_project_file(project_id: str, path: str = Query(...), content: str = Body(..., embed=True)):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    file_path = project_path / path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    file_path.write_text(content, encoding='utf-8')
    return {"status": "ok", "message": "Archivo actualizado"}

@router.post("/projects/{project_id}/execute")
def execute_project_endpoint(project_id: str):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    result = {
        "success": False,
        "stdout": "",
        "stderr": "",
        "execution_type": "desconocido",
        "url": None,
        "dependencies_installed": False,
        "steps": []
    }

    req_file = project_path / "backend" / "requirements.txt"
    if not req_file.exists():
        req_file = project_path / "requirements.txt"

    if req_file.exists():
        result["steps"].append("📦 Instalando dependencias...")
        try:
            install_result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                capture_output=True, text=True, timeout=60
            )
            if install_result.returncode == 0:
                result["dependencies_installed"] = True
                result["steps"].append("✅ Dependencias instaladas correctamente.")
            else:
                result["stderr"] = install_result.stderr
                result["steps"].append(f"❌ Error al instalar dependencias:\n{install_result.stderr}")
                return result
        except subprocess.TimeoutExpired:
            result["stderr"] = "Timeout instalando dependencias."
            result["steps"].append("❌ Timeout instalando dependencias.")
            return result
    else:
        result["steps"].append("⚠️ No se encontró requirements.txt. Omitiendo instalación de dependencias.")

    executor = ProjectExecutor(str(project_path))
    exec_result = executor.execute_project()

    result["success"] = exec_result.get("success", False)
    result["stdout"] = exec_result.get("stdout", "")
    result["stderr"] = exec_result.get("stderr", "")
    result["execution_type"] = exec_result.get("execution_type", "desconocido")

    if result["success"]:
        result["url"] = "http://localhost:8001"
        result["steps"].append(f"✅ Proyecto iniciado en {result['url']}")
        result["steps"].append("🔗 Abrí la pestaña 'Vista previa' para verlo.")
    else:
        result["steps"].append(f"❌ Falló la ejecución:\n{result['stderr'] or result['stdout']}")

    return result

@router.get("/projects/{project_id}/chat")
def get_project_chat(project_id: str):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    chat_path = project_path / "chat.json"
    if chat_path.exists():
        return json_module.loads(chat_path.read_text(encoding='utf-8'))
    return {"messages": []}

@router.post("/projects/{project_id}/chat")
async def save_project_chat(project_id: str, request: Request):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    chat_path = project_path / "chat.json"
    body = await request.json()
    chat_path.write_text(json_module.dumps(body, indent=2), encoding='utf-8')
    return {"status": "ok"}

@router.put("/projects/{project_id}/name")
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

@router.get("/projects/{project_id}/name")
def get_project_name(project_id: str):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    meta_path = project_path / "project.json"
    if meta_path.exists():
        meta = json_module.loads(meta_path.read_text(encoding='utf-8'))
        return {"name": meta.get("name", project_id)}
    return {"name": project_id}

@router.get("/projects/{project_id}/audit")
def audit_project(project_id: str):
    project_path = project_manager.get_project_path(project_id)
    if not project_path:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    from core.project_auditor import ProjectAuditor
    auditor = ProjectAuditor(str(project_path))
    issues = auditor.audit()
    return {"project_id": project_id, "issues": issues, "status": "ok" if not issues else "attention"}