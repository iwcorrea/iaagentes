"""
Fase 4/5: Tests y Despliegue.
Genera pruebas unitarias y archivos de infraestructura.
Ejecuta linters automáticos al final para asegurar calidad.
"""
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional

from crewai import Agent, Task, Crew
from core.agent_cache import AgentCache
from core.project_memory import ProjectMemory  # solo para type hint


class PhaseDeploy:
    def __init__(self, workspace_path: Path, agent_cache: AgentCache, memory: Optional[ProjectMemory] = None):
        self.workspace_path = workspace_path
        self.agent_cache = agent_cache
        self.memory = memory  # opcional, para registrar issues de linters

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
                "No sobrescribas los archivos originales. "
                "Responde con un JSON donde cada clave sea la ruta del archivo de test y el valor sea el código fuente (string)."
            ),
            agent=tester,
            expected_output="JSON con archivos de tests (ruta: código)."
        )

        crew = Crew(agents=[tester], tasks=[task], verbose=True)
        crew.kickoff()

        raw = task.output.raw if hasattr(task.output, 'raw') else str(task.output)
        files = self._extract_files_robust(raw)

        saved = {}
        tests_dir = self.workspace_path / "tests"
        for file_path, content in files.items():
            if not isinstance(content, str):
                print(f"⚠️ Valor inesperado para {file_path}: {type(content)}. Omitiendo.")
                continue
            test_path = tests_dir / file_path.replace("tests/", "").replace("testingTechCorp/", "").replace("landingTechCorp/", "")
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(content, encoding='utf-8')
            saved[str(test_path.relative_to(self.workspace_path))] = content

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
                "Responde con un JSON donde las claves sean los nombres de archivo y los valores sean el contenido completo como string. "
                "No anides objetos; solo strings."
            ),
            agent=deployer,
            expected_output="JSON con archivos de despliegue."
        )

        crew = Crew(agents=[deployer], tasks=[task], verbose=True)
        crew.kickoff()

        raw = task.output.raw if hasattr(task.output, 'raw') else str(task.output)
        files = self._extract_files_robust(raw)

        saved = {}
        for file_path, content in files.items():
            if not isinstance(content, str):
                print(f"⚠️ Valor inesperado para {file_path}: {type(content)}. Omitiendo.")
                continue
            full_path = self.workspace_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            saved[file_path] = content

        print(f"🚀 Archivos de despliegue guardados: {list(saved.keys())}")

        # --- Linters automáticos (si hay memoria disponible) ---
        if self.memory:
            try:
                from tools.project_finalizer import run_linters
                lint_issues = run_linters(str(self.workspace_path))
                for issue in lint_issues:
                    self.memory.add_audit_issue(
                        file=issue["file"],
                        line=issue.get("line", 0),
                        message=issue["message"],
                        severity=issue.get("severity", "warning")
                    )
                print(f"🔍 Linters encontraron {len(lint_issues)} issues.")
            except ImportError:
                print("⚠️ Módulo tools.project_finalizer no encontrado. Omitiendo linters.")
        else:
            print("ℹ️ Memoria no disponible. Omitiendo linters.")

        return {"files": saved}

    def _extract_files_robust(self, raw_text: str) -> Dict[str, str]:
        raw_text = raw_text.strip()

        try:
            data = json.loads(raw_text)
            if isinstance(data, dict):
                return self._flatten_content_values(data)
        except:
            pass

        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict):
                    return self._flatten_content_values(data)
            except:
                pass

        files = {}
        pattern = re.findall(
            r'["\']?([\w\-./\\]+\.\w+)["\']?\s*:::\s*(.*?)(?=\n\S+:::\s|\Z)',
            raw_text, re.DOTALL
        )
        for path, code in pattern:
            files[path.strip()] = code.strip()
        return files

    def _flatten_content_values(self, data: Dict[str, Any]) -> Dict[str, str]:
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = value
            elif isinstance(value, dict):
                if 'content' in value:
                    result[key] = value['content']
                elif 'code' in value:
                    result[key] = value['code']
                else:
                    for v in value.values():
                        if isinstance(v, str):
                            result[key] = v
                            break
            else:
                result[key] = str(value)
        return result