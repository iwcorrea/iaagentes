"""
Fase 1: Generación de código.
Utiliza ProjectMemory para evitar alucinaciones y duplicados.
Inyecta instrucciones desde documentos .md del proyecto.
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
        # Contexto existente
        context = self.memory.get_manifest_summary()
        design = self.memory.get_design_context()
        full_context = f"{context}\n{design}" if design else context

        # Instrucciones documentales
        director_instructions = self.memory.get_instructions_for_agent("director")
        backend_instructions = self.memory.get_instructions_for_agent("backend")
        frontend_instructions = self.memory.get_instructions_for_agent("frontend")

        # Prompt para el Director
        director_prompt = user_prompt
        if director_instructions:
            director_prompt = f"{director_instructions}\n\n🔧 TAREA: {user_prompt}"
        if full_context and "vacío" not in full_context:
            director_prompt += f"\n\n{full_context}\nBasate en los archivos existentes. No dupliques."

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
                f"Requerimiento:\n{director_prompt}\n\n"
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

        for note in design_notes:
            self.memory.add_design_decision(note)

        if not plan:
            print("❌ No se pudo extraer el plan. Abortando.")
            return {"files": {}}

        new_files = [f for f in plan if not self.memory.file_exists(f["path"])]
        print(f"📁 Archivos nuevos a generar: {len(new_files)} (ya existían {len(plan) - len(new_files)})")

        if not new_files:
            print("✅ Todos los archivos ya existen. Nada que generar.")
            return {"files": {}}

        files = {}
        # Preparar agentes con instrucciones personalizadas
        backend_agent = self._create_agent_with_instructions(
            "backend",
            backend_instructions,
            role="Desarrollador Backend Python",
            goal="Generar código Python/FastAPI de alta calidad.",
            backstory="Eres un desarrollador backend experto en FastAPI."
        )
        frontend_agent = self._create_agent_with_instructions(
            "frontend",
            frontend_instructions,
            role="Desarrollador Frontend React",
            goal="Generar componentes React con Tailwind CSS.",
            backstory="Eres un desarrollador frontend experto en React y Tailwind."
        )

        backend_files = [f for f in new_files if f["path"].endswith((".py", ".txt"))]
        frontend_files = [f for f in new_files if f["path"].endswith((".jsx", ".tsx", ".css", ".json", ".js"))]

        if backend_files:
            files.update(self._generate_code_for_files(backend_files, backend_agent, "Backend"))
        if frontend_files:
            files.update(self._generate_code_for_files(frontend_files, frontend_agent, "Frontend"))

        if not files:
            print("❌ No se generaron archivos.")
            return {"files": {}}

        print(f"✅ Generados {len(files)} archivos en total.")
        return {"files": files}

    def _create_agent_with_instructions(self, agent_name: str, instructions: str, **kwargs):
        """Crea un agente añadiendo instrucciones documentales a su backstory o goal."""
        if instructions:
            original_backstory = kwargs.get("backstory", "")
            kwargs["backstory"] = f"{original_backstory}\n\n📚 Sigue estas instrucciones del proyecto:\n{instructions}"
        return self.agent_cache.get_or_create(
            agent_name,
            lambda: Agent(**kwargs, verbose=True, allow_delegation=False)
        )

    def _get_raw_output(self, task_output) -> str:
        return task_output.raw if hasattr(task_output, 'raw') else str(task_output)

    def _extract_plan(self, raw: str) -> dict:
        return self._extract_json_from_text(raw) or {}

    def _generate_code_for_files(self, file_entries: list, agent: Agent, category: str) -> Dict[str, str]:
        file_list = "\n".join([f"- {f['path']}: {f['purpose']}" for f in file_entries])
        task_desc = (
            f"Genera el código completo para los siguientes archivos {category}.\n"
            f"{file_list}\n\n"
            "Responde EXCLUSIVAMENTE con un JSON donde las claves son las rutas de los archivos "
            "y los valores son el código fuente completo.\n"
            "Ejemplo: {{\"ruta/archivo.py\": \"código aquí\"}}"
        )
        task = Task(description=task_desc, agent=agent, expected_output="JSON con archivos generados.")

        for attempt in range(1, 3):
            try:
                crew = Crew(agents=[agent], tasks=[task], verbose=True)
                crew.kickoff()
                raw = self._get_raw_output(task.output)
                files = self._robust_extract_files(raw)
                if files:
                    return files
                print(f"⚠️ Intento {attempt}: no se pudo extraer archivos. Reintentando...")
            except Exception as e:
                print(f"❌ Intento {attempt} falló: {e}")
                if attempt == 2:
                    return {}
        return {}

    def _robust_extract_files(self, raw_text: str) -> Dict[str, str]:
        """
        Extrae un mapeo ruta -> código de la salida del agente.
        Maneja JSON puro, bloques de código markdown, backticks en lugar de comillas,
        y patrones ruta:::código.
        """
        raw_text = raw_text.strip()

        # 1. Intentar extraer el objeto JSON balanceado
        balanced_json = self._extract_json_from_text(raw_text)
        if balanced_json and isinstance(balanced_json, dict):
            if any('/' in k or '\\' in k for k in balanced_json.keys()):
                return balanced_json

        # 2. Buscar dentro de bloques ```json ... ```
        block_match = re.search(r'```json\s*\n(.*?)\n```', raw_text, re.DOTALL)
        if block_match:
            inner_json = self._extract_json_from_text(block_match.group(1))
            if inner_json and isinstance(inner_json, dict):
                if any('/' in k or '\\' in k for k in inner_json.keys()):
                    return inner_json

        # 3. Sanitizar backticks que el modelo usa como comillas
        sanitized = raw_text.replace('`', '"')
        balanced_sanitized = self._extract_json_from_text(sanitized)
        if balanced_sanitized and isinstance(balanced_sanitized, dict):
            if any('/' in k or '\\' in k for k in balanced_sanitized.keys()):
                return balanced_sanitized

        # 4. Último recurso: patrones ruta:::código
        files = {}
        pattern = re.findall(
            r'["\']?([\w\-./\\]+\.\w+)["\']?\s*:::\s*(.*?)(?=\n\S+:::\s|\Z)',
            raw_text, re.DOTALL
        )
        for path, code in pattern:
            files[path.strip()] = code.strip()

        return files

    @staticmethod
    def _extract_json_from_text(text: str) -> Any:
        """
        Encuentra la primera llave de apertura y extrae el objeto JSON balanceado,
        ignorando cualquier texto alrededor.
        """
        start = text.find('{')
        if start == -1:
            return None

        count = 0
        end = start
        for i, ch in enumerate(text[start:], start=start):
            if ch == '{':
                count += 1
            elif ch == '}':
                count -= 1
                if count == 0:
                    end = i + 1
                    break

        if count == 0:
            json_str = text[start:end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                try:
                    return json.loads(json_str.replace('\n', '\\n'))
                except:
                    pass
        return None