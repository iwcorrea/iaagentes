"""
Fase 3: Gestión de dependencias.
Instala los paquetes listados en requirements.txt (si existe) y cachea la información.
"""
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

from core.agent_cache import AgentCache
from core.dependency_cache import DependencyCache


class PhaseDependencies:
    def __init__(self, workspace_path: Path, agent_cache: AgentCache):
        self.workspace_path = workspace_path
        self.agent_cache = agent_cache
        self.dep_cache = DependencyCache()

    def execute(self, manifest_context: str = "") -> Dict[str, Any]:
        req_file = self.workspace_path / "backend" / "requirements.txt"
        if not req_file.exists():
            req_file = self.workspace_path / "requirements.txt"

        if req_file.exists():
            print(f"📦 Instalando dependencias desde {req_file}...")
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode == 0:
                    print("✅ Dependencias instaladas correctamente.")
                    # Cachear las dependencias
                    deps = req_file.read_text().splitlines()
                    self.dep_cache.add_batch(self.workspace_path.name, deps)
                else:
                    print(f"⚠️ Error instalando dependencias:\n{result.stderr}")
            except subprocess.TimeoutExpired:
                print("⏰ Timeout instalando dependencias.")
        else:
            print("ℹ️ No se encontró requirements.txt. Omitiendo instalación.")

        return {"dependencies_installed": req_file.exists()}