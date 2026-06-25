"""
Fase 5 (reparación): Corrige issues reportados en la auditoría
utilizando ProjectMemory como fuente de verdad.
"""
import re
from pathlib import Path
from typing import Dict, Any

from crewai import Agent, Task, Crew
from core.agent_cache import AgentCache
from core.project_memory import ProjectMemory


class PhaseRepair:
    def __init__(self, workspace_path: Path, agent_cache: AgentCache, memory: ProjectMemory):
        self.workspace_path = workspace_path
        self.agent_cache = agent_cache
        self.memory = memory

    def execute(self) -> Dict[str, Any]:
        pending_issues = self.memory.get_pending_issues()
        if not pending_issues:
            print("✅ No hay issues pendientes. Nada que reparar.")
            return {"fixed": 0}

        repair_agent = self.agent_cache.get_or_create(
            "repair",
            lambda: Agent(
                role="Ingeniero de Reparación",
                goal="Corregir errores puntuales en archivos de código según issues de auditoría.",
                backstory="Eres un desarrollador meticuloso que aplica correcciones quirúrgicas sin romper el resto del código.",
                verbose=True,
                allow_delegation=False,
            )
        )

        fixed_count = 0

        for idx, issue in enumerate(pending_issues):
            file_path = issue["file"]
            line = issue.get("line", 0)
            message = issue.get("message", "")
            severity = issue.get("severity", "warning")

            full_path = self.workspace_path / file_path
            if not full_path.exists():
                print(f"⚠️ El archivo {file_path} no existe. Saltando issue.")
                continue

            original_code = full_path.read_text(encoding='utf-8')

            task_desc = (
                f"Archivo: {file_path}\n"
                f"Línea aproximada: {line}\n"
                f"Problema: {message}\n"
                f"Severidad: {severity}\n\n"
                "Código actual del archivo:\n"
                f"```\n{original_code}\n```\n\n"
                "Devuelve EXCLUSIVAMENTE el código completo del archivo ya corregido. "
                "No cambies nada que no sea necesario para resolver el issue."
            )

            task = Task(
                description=task_desc,
                agent=repair_agent,
                expected_output="Código corregido del archivo."
            )

            try:
                crew = Crew(agents=[repair_agent], tasks=[task], verbose=True)
                crew.kickoff()

                raw_output = task.output.raw if hasattr(task.output, 'raw') else str(task.output)

                # Limpiar backticks de markdown si el agente los incluyó
                new_code = raw_output.strip()
                if "```" in new_code:
                    match = re.search(r'```(?:\w+)?\n(.*?)```', new_code, re.DOTALL)
                    if match:
                        new_code = match.group(1).strip()

                # Guardar la corrección en disco
                full_path.write_text(new_code, encoding='utf-8')

                # Actualizar la memoria
                self.memory.add_file(file_path, new_code, "Reparado (corrección de auditoría)")
                self.memory.mark_issue_fixed(idx)
                fixed_count += 1
                print(f"✅ Issue corregido en {file_path}: {message}")

            except Exception as e:
                print(f"❌ No se pudo corregir issue en {file_path}: {e}")

        print(f"🔧 Reparación completada. Issues corregidos: {fixed_count}")
        return {"fixed": fixed_count}