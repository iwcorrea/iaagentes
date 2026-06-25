"""
Fase 4/5: Tests y Despliegue.
Genera pruebas unitarias básicas y archivos de infraestructura.
Ahora persiste los archivos generados en disco.
"""
from pathlib import Path
from typing import Dict, Any

from crewai import Agent, Task, Crew
from core.agent_cache import AgentCache


class PhaseDeploy:
    def __init__(self, workspace_path: Path, agent_cache: AgentCache):
        self.workspace_path = workspace_path
        self.agent_cache = agent_cache

    def execute(self, manifest_context: str = "", stage: str = "tests") -> Dict[str, Any]:
        if stage == "tests":
            return self._run_tests_phase(manifest_context)
        else:
            return self._run_deploy_phase(manifest_context)

    def _run_tests_phase(self, manifest_context: str) -> Dict[str, Any]:
        tester = self.agent_cache.get_or_create(
            "tester",
            lambda: Agent(
                role="Ingeniero de Pruebas",
                goal="Generar pruebas unitarias con pytest para los módulos backend existentes.",
                backstory="Eres un QA automation experto en pytest. Creas tests claros y efectivos.",
                verbose=True,
                allow_delegation=False,
            )
        )

        task = Task(
            description=(
                f"Genera pruebas unitarias para los archivos del proyecto.\n{manifest_context}\n\n"
                "Escribe los tests en archivos separados dentro de 'tests/'. "
                "Para cada módulo importante, crea al menos un test de funcionamiento básico. "
                "Responde con un JSON donde cada clave sea la ruta del archivo de test y el valor sea el código."
            ),
            agent=tester,
            expected_output="JSON con archivos de tests (ruta: código)."
        )

        crew = Crew(agents=[tester], tasks=[task], verbose=True)
        result = crew.kickoff()

        # Extraer archivos de tests usando el mismo extractor robusto
        from core.phases.phase_generator import PhaseGenerator as PG
        raw = result.raw if hasattr(result, 'raw') else str(result)
        files = PG._robust_extract_files(PG, raw)  # instancia dummy para usar método estático

        saved = {}
        for file_path, content in files.items():
            full_path = self.workspace_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            saved[file_path] = content

        print(f"🧪 Archivos de tests guardados: {list(saved.keys())}")
        return {"files": saved}

    def _run_deploy_phase(self, manifest_context: str) -> Dict[str, Any]:
        deployer = self.agent_cache.get_or_create(
            "deployer",
            lambda: Agent(
                role="Ingeniero DevOps",
                goal="Crear archivos de despliegue (Dockerfile, docker-compose, .env.example, README).",
                backstory="Eres un especialista en contenedores y documentación. Tus entregables son impecables.",
                verbose=True,
                allow_delegation=False,
            )
        )

        task = Task(
            description=(
                f"Genera los archivos de infraestructura necesarios.\n{manifest_context}\n\n"
                "Crea: Dockerfile, docker-compose.yml, .env.example y README.md.\n"
                "Responde con un JSON donde las claves sean los nombres de archivo y los valores el contenido."
            ),
            agent=deployer,
            expected_output="JSON con archivos de despliegue."
        )

        crew = Crew(agents=[deployer], tasks=[task], verbose=True)
        result = crew.kickoff()

        from core.phases.phase_generator import PhaseGenerator as PG
        raw = result.raw if hasattr(result, 'raw') else str(result)
        files = PG._robust_extract_files(PG, raw)

        saved = {}
        for file_path, content in files.items():
            full_path = self.workspace_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            saved[file_path] = content

        print(f"🚀 Archivos de despliegue guardados: {list(saved.keys())}")
        return {"files": saved}