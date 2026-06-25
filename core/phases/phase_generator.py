"""
Fase 1: Generación de código.
Utiliza el Director Agent para planificar la arquitectura y luego
los agentes Backend y Frontend para generar los archivos.
Extrae código de respuestas JSON o de texto libre (fallback robusto).
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from crewai import Agent, Task, Crew
from core.agent_cache import AgentCache


class PhaseGenerator:
    def __init__(self, workspace_path: Path, agent_cache: AgentCache):
        self.workspace_path = workspace_path
        self.agent_cache = agent_cache

    def execute(self, user_prompt: str, manifest_context: str = "") -> Dict[str, Any]:
        if manifest_context:
            full_prompt = (
                f"{manifest_context}\n\n"
                f"🔧 TAREA: {user_prompt}\n\n"
                "Basate en los archivos ya existentes para no duplicarlos. "
                "Genera solo el código necesario para completar la tarea."
            )
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

        backend_dev = self.agent_cache.get_or_create(
            "backend",
            lambda: Agent(
                role="Desarrollador Backend Python",
                goal="Generar código Python/FastAPI de alta calidad siguiendo el plan del arquitecto.",
                backstory="Eres un desarrollador backend experto en FastAPI, SQLAlchemy y Pydantic.",
                verbose=True,
                allow_delegation=False,
            )
        )

        frontend_dev = self.agent_cache.get_or_create(
            "frontend",
            lambda: Agent(
                role="Desarrollador Frontend React",
                goal="Generar componentes React con Tailwind CSS según el plan del arquitecto.",
                backstory="Eres un desarrollador frontend experto en React, Vite y Tailwind CSS.",
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
                '  ]\n'
                "}\n"
                "No incluyas ningún texto fuera del JSON."
            ),
            agent=director,
            expected_output="JSON con el plan de archivos."
        )

        backend_task = Task(
            description=(
                "Genera el código completo de cada archivo backend listado en el plan. "
                "Formato de salida: JSON con mapeo ruta -> código.\n"
                "Ejemplo:\n"
                '{"backend/main.py": "from fastapi import FastAPI\\n...", ...}\n'
                "Asegura que el código sea funcional, importe correctamente y siga el plan."
            ),
            agent=backend_dev,
            expected_output="JSON con los archivos backend.",
            context=[plan_task]
        )

        frontend_task = Task(
            description=(
                "Genera el código completo de cada archivo frontend listado en el plan. "
                "Formato de salida: JSON con mapeo ruta -> código.\n"
                "Asegura que los componentes React sean funcionales y utilicen Tailwind CSS."
            ),
            agent=frontend_dev,
            expected_output="JSON con los archivos frontend.",
            context=[plan_task]
        )

        crew = Crew(
            agents=[director, backend_dev, frontend_dev],
            tasks=[plan_task, backend_task, frontend_task],
            verbose=True
        )

        crew_output = crew.kickoff()

        # Extraer plan para referencia (no se guarda como archivo)
        plan_raw = self._get_raw_output(plan_task.output)
        print("📋 Plan de generación:", plan_raw[:200] + "..." if len(plan_raw) > 200 else plan_raw)

        files = {}

        # Intentar parsear salida del backend
        backend_json = self._robust_extract_files(self._get_raw_output(backend_task.output))
        if isinstance(backend_json, dict):
            files.update(backend_json)

        # Intentar parsear salida del frontend
        frontend_json = self._robust_extract_files(self._get_raw_output(frontend_task.output))
        if isinstance(frontend_json, dict):
            files.update(frontend_json)

        if not files:
            print("❌ No se generaron archivos. Revisa los logs de los agentes.")
            return {"files": {}}

        print(f"✅ Generados {len(files)} archivos en total.")
        return {"files": files}

    def _get_raw_output(self, task_output) -> str:
        """Obtiene el texto crudo de la salida de un agente."""
        return task_output.raw if hasattr(task_output, 'raw') else str(task_output)

    def _robust_extract_files(self, raw_text: str) -> Dict[str, str]:
        """
        Intenta extraer un mapeo ruta -> código de la salida del agente.
        Soporta JSON bien formado, bloques de código Markdown, y formato ruta:::código.
        """
        raw_text = raw_text.strip()

        # 1. Intentar JSON puro
        try:
            result = json.loads(raw_text)
            if isinstance(result, dict):
                # Si es un dict con keys que parecen rutas, asumimos que es el mapeo
                if any('/' in k or '\\' in k for k in result.keys()):
                    return result
                # Si tiene una key 'files', 'backend' o similar
                for key in ['files', 'backend', 'frontend', 'code']:
                    if key in result and isinstance(result[key], dict):
                        return result[key]
        except json.JSONDecodeError:
            pass

        # 2. Intentar extraer JSON de un bloque de código
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                if isinstance(result, dict):
                    if any('/' in k or '\\' in k for k in result.keys()):
                        return result
            except:
                pass

        # 3. Buscar bloques de código con nombre de archivo (formato ruta:::código)
        # Patrón: "ruta/archivo.py" seguido de código entre backticks
        file_pattern = re.findall(
            r'["\']?([\w\-./\\]+\.(?:py|js|jsx|tsx|css|html|json|yaml|yml|txt|md|env))["\']?\s*[:=]+\s*```(.*?)```',
            raw_text, re.DOTALL
        )
        files = {}
        for filepath, code in file_pattern:
            files[filepath.strip()] = code.strip()

        if files:
            return files

        # 4. Último recurso: buscar patrones "ruta:::código" sin backticks
        manual_pattern = re.findall(
            r'([\w\-./\\]+\.(?:py|js|jsx|tsx|css|html|json|yaml|yml|txt|md|env))\s*:::?\s*(.*?)(?=\n[\w\-./\\]+\.\w+\s*:::|$)',
            raw_text, re.DOTALL
        )
        for filepath, code in manual_pattern:
            files[filepath.strip()] = code.strip()

        return files