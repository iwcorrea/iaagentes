"""
Fase 1: Generación de código.
Utiliza ProjectMemory para evitar alucinaciones y duplicados.
"""
import json
import re
from pathlib import Path
from typing import Dict, Any

from crewai import Agent, Task, Crew
from core.agent_cache import AgentCache
from core.project_memory import ProjectMemory


class PhaseGenerator:
    def __init__(self, workspace_path: Path, agent_cache: AgentCache, memory: ProjectMemory):
        self.workspace_path = workspace_path
        self.agent_cache = agent_cache
        self.memory = memory

    def execute(self, user_prompt: str) -> Dict[str, Any]:
        # Construir contexto a partir de la memoria
        context = self.memory.get_manifest_summary()
        design = self.memory.get_design_context()
        full_context = f"{context}\n{design}" if design else context

        if full_context and "vacío" not in full_context:
            full_prompt = f"{full_context}\n\n🔧 TAREA: {user_prompt}\n\nBasate en los archivos existentes. No dupliques."
        else:
            full_prompt = user_prompt

        director = self.agent_cache.get_or_create(
            "director",
            lambda: Agent(
                role="Arquitecto de Software",
                goal="Planificar la estructura de archivos necesaria para implementar el requerimiento del usuario.",
                backstory="Eres un arquitecto senior experto en diseño de aplicaciones web con FastAPI y React.",
                verbose=True,
                allow_delegation=False,
            )
        )

        plan_task = Task(
            description=(
                f"Analiza el siguiente requerimiento y genera un plan de archivos JSON.\n"
                f"Requerimiento:\n{full_prompt}\n\n"
                "Responde EXCLUSIVAMENTE con un JSON válido con esta estructura:\n"
                "{\n"
                '  "plan": [\n'
                '    {"path": "ruta/archivo.py", "purpose": "descripción breve"},\n'
                '    ...\n'
                '  ],\n'
                '  "design_notes": ["lista de decisiones de diseño importantes"]\n'
                "}\n"
                "No incluyas ningún texto fuera del JSON."
            ),
            agent=director,
            expected_output="JSON con el plan de archivos."
        )

        crew_plan = Crew(agents=[director], tasks=[plan_task], verbose=True)
        crew_plan.kickoff()
        plan_raw = self._get_raw_output(plan_task.output)
        print("📋 Plan de generación:", plan_raw[:300])

        plan_data = self._extract_plan(plan_raw)
        plan = plan_data.get("plan", [])
        design_notes = plan_data.get("design_notes", [])

        # Guardar decisiones de diseño en memoria
        for note in design_notes:
            self.memory.add_design_decision(note)

        if not plan:
            print("❌ No se pudo extraer el plan. Abortando.")
            return {"files": {}}

        # Filtrar archivos que ya existen (evitar alucinaciones)
        new_files = []
        for f in plan:
            if not self.memory.file_exists(f["path"]):
                new_files.append(f)
        print(f"📁 Archivos nuevos a generar: {len(new_files)} (ya existían {len(plan) - len(new_files)})")

        if not new_files:
            print("✅ Todos los archivos ya existen. Nada que generar.")
            return {"files": {}}

        files = {}
        backend_agent = self.agent_cache.get_or_create(
            "backend",
            lambda: Agent(
                role="Desarrollador Backend Python",
                goal="Generar código Python/FastAPI de alta calidad.",
                backstory="Eres un desarrollador backend experto en FastAPI.",
                verbose=True,
                allow_delegation=False,
            )
        )

        backend_files = [f for f in new_files if f["path"].endswith(".py") or f["path"].endswith(".txt")]
        frontend_files = [f for f in new_files if f["path"].endswith((".jsx", ".tsx", ".css", ".json"))]

        if backend_files:
            code = self._generate_code_for_files(backend_files, backend_agent, "Backend")
            files.update(code)

        if frontend_files:
            frontend_agent = self.agent_cache.get_or_create(
                "frontend",
                lambda: Agent(
                    role="Desarrollador Frontend React",
                    goal="Generar componentes React con Tailwind CSS.",
                    backstory="Eres un desarrollador frontend experto en React y Tailwind.",
                    verbose=True,
                    allow_delegation=False,
                )
            )
            code = self._generate_code_for_files(frontend_files, frontend_agent, "Frontend")
            files.update(code)

        if not files:
            print("❌ No se generaron archivos.")
            return {"files": {}}

        print(f"✅ Generados {len(files)} archivos en total.")
        return {"files": files}

    def _get_raw_output(self, task_output) -> str:
        return task_output.raw if hasattr(task_output, 'raw') else str(task_output)

    def _extract_plan(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return {}

    def _generate_code_for_files(self, file_entries: list, agent: Agent, category: str) -> Dict[str, str]:
        file_list = "\n".join([f"- {f['path']}: {f['purpose']}" for f in file_entries])
        task_desc = (
            f"Genera el código completo para los siguientes archivos {category}.\n"
            f"{file_list}\n\n"
            "Responde EXCLUSIVAMENTE con un JSON donde las claves son las rutas de los archivos "
            "y los valores son el código fuente completo.\n"
            "Ejemplo: {{\"ruta/archivo.py\": \"código aquí\"}}"
        )
        task = Task(
            description=task_desc,
            agent=agent,
            expected_output="JSON con archivos generados."
        )

        max_retries = 2
        for attempt in range(1, max_retries + 1):
            try:
                crew = Crew(agents=[agent], tasks=[task], verbose=True)
                crew.kickoff()
                raw = self._get_raw_output(task.output)
                files = self._robust_extract_files(raw)
                if files:
                    return files
                else:
                    print(f"⚠️ Intento {attempt}: no se pudo extraer archivos. Reintentando...")
            except Exception as e:
                print(f"❌ Intento {attempt} falló con error: {e}")
                if attempt == max_retries:
                    return {}
        return {}

    def _robust_extract_files(self, raw_text: str) -> Dict[str, str]:
        raw_text = raw_text.strip()
        try:
            result = json.loads(raw_text)
            if isinstance(result, dict):
                if any('/' in k or '\\' in k for k in result.keys()):
                    return result
        except:
            pass
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                if isinstance(result, dict):
                    return result
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