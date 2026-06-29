import subprocess
import sys
from pathlib import Path
from typing import List, Dict

def run_linters(project_path: str) -> List[Dict[str, str]]:
    """Ejecuta linters sobre el backend del proyecto y devuelve una lista de issues."""
    issues = []
    backend = Path(project_path) / "backend"
    if not backend.exists():
        backend = Path(project_path)
    # Flake8
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(backend), "--exit-zero", "--max-line-length=120"],
            capture_output=True, text=True, timeout=30
        )
        for line in result.stdout.strip().splitlines():
            if line:
                parts = line.split(":", 3)
                if len(parts) >= 3:
                    issues.append({"file": parts[0], "line": int(parts[1]), "message": parts[2].strip(), "severity": "warning"})
    except Exception as e:
        issues.append({"file": "", "line": 0, "message": f"Flake8 error: {str(e)}", "severity": "error"})
    return issues

def git_init_and_push(project_path: str, remote_url: str = None) -> bool:
    """Inicializa git y hace push si se proporciona remote_url."""
    repo = Path(project_path)
    if not (repo / ".git").exists():
        subprocess.run(["git", "init"], cwd=project_path, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=project_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "AI-ECOSYSTEM generated project"], cwd=project_path, capture_output=True)
    if remote_url:
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=project_path, capture_output=True)
        result = subprocess.run(["git", "push", "-u", "origin", "master"], cwd=project_path, capture_output=True, text=True)
        return result.returncode == 0
    return True