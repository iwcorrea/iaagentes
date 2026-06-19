"""Verifica que la estructura del proyecto esté completa."""
from pathlib import Path

ROOT = Path(__file__).parent

expected_structure = {
    "api/main.py": True,
    "api/routers/projects_router.py": True,
    "agents/director_agent.py": True,
    "agents/backend_agent.py": True,
    "agents/frontend_agent.py": True,
    "agents/qa_agent.py": True,
    "agents/repair_agent.py": True,
    "agents/dependency_agent.py": True,
    "agents/test_agent.py": True,
    "agents/deploy_agent.py": True,
    "core/architect_orchestrator.py": True,
    "core/phases/__init__.py": True,
    "core/phases/phase_generator.py": True,
    "core/phases/phase_auditor.py": True,
    "core/phases/phase_dependencies.py": True,
    "core/phases/phase_deploy.py": True,
    "core/phases/phase_repair.py": True,
    "core/syntax_validator.py": True,
    "core/dependency_cache.py": True,
    "core/learning_tracker.py": True,
    "tools/custom_tools.py": True,
    "tools/memory_tools.py": True,
    "tools/code_cleaner.py": True,
    "validate_ecosystem.py": True,
    "organize_project.py": True,
    "tests/test_tools.py": True,
}

missing = []
for path, required in expected_structure.items():
    if required and not (ROOT / path).exists():
        missing.append(path)

if missing:
    print(f"Faltan {len(missing)} archivos:")
    for m in missing:
        print(f"  - {m}")
else:
    print("✅ Estructura del proyecto completa.")