"""Valida que todos los imports del ecosistema sean correctos."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

errors = []

modules = [
    "api.main",
    "api.routers.projects_router",
    "core.architect_orchestrator",
    "core.syntax_validator",
    "core.dependency_cache",
    "core.prompt_guard",
    "core.learning_tracker",
    "agents.test_agent",
    "agents.deploy_agent",
]

for mod_name in modules:
    try:
        __import__(mod_name)
        print(f"✅ {mod_name}")
    except Exception as e:
        errors.append(f"❌ {mod_name}: {e}")

if errors:
    print(f"\nSe encontraron {len(errors)} errores:")
    for error in errors:
        print(f"  {error}")
else:
    print(f"\n✅ Todos los módulos ({len(modules)}) importados correctamente.")