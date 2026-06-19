"""Valida que todos los imports del ecosistema sean correctos."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

errors = []

modules = [
    # API
    "api.main",
    "api.routers.projects_router",
    
    # Core principal
    "core.architect_orchestrator",
    "core.architecture_memory",
    "core.executor",
    "core.refactor_engine",
    "core.global_context",
    "core.plan_validator",
    "core.project_auditor",
    "core.code_reviewer",
    "core.prompt_integrity",
    "core.learning_tracker",
    "core.syntax_validator",
    "core.dependency_cache",
    "core.agent_status",
    "core.agent_scanner",
    "core.improvement_queue",
    "core.meta_agent",
    "core.sandbox",
    "core.project_manager",
    "core.quality_metrics",
    "core.config_assistant",
    "core.guided_builder",
    "core.prompt_guard",
    "core.router",
    "core.file_generator",
    
    # Fases modulares
    "core.phases.phase_generator",
    "core.phases.phase_auditor",
    "core.phases.phase_dependencies",
    "core.phases.phase_deploy",
    "core.phases.phase_repair",
    
    # Agentes
    "agents.director_agent",
    "agents.backend_agent",
    "agents.frontend_agent",
    "agents.qa_agent",
    "agents.repair_agent",
    "agents.dependency_agent",
    "agents.test_agent",
    "agents.deploy_agent",
    
    # Workflows y tools
    "workflows.ecommerce_workflow",
    "tools.custom_tools",
    "tools.memory_tools",
    "tools.code_cleaner",
]

for mod_name in modules:
    try:
        __import__(mod_name)
        print(f"✅ {mod_name}")
    except Exception as e:
        errors.append(f"❌ {mod_name}: {e}")

if errors:
    print(f"\n⚠️  Se encontraron {len(errors)} errores:")
    for error in errors:
        print(f"  {error}")
else:
    print(f"\n✅ Todos los módulos ({len(modules)}) importados correctamente.")