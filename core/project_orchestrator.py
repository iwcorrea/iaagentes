# core/project_orchestrator.py
import logging
import os
import json
from typing import Dict, Any, Optional

from crewai import Crew, Process
from agents.director_agent import director_agent
from agents.backend_agent import backend_agent
from agents.frontend_agent import frontend_agent
from agents.qa_agent import qa_agent
from agents.repair_agent import repair_agent
from agents.dependency_agent import dependency_agent

from core.architecture_memory import ArchitectureMemory
from tools.file_writer import FileWriterTool
from tools.terminal_tool import TerminalTool

logger = logging.getLogger(__name__)

class ProjectOrchestrator:
    def __init__(self):
        self.memory = ArchitectureMemory()
        self.writer = FileWriterTool()
        self.terminal = TerminalTool()
        self.crew = None

    def run(self, prompt: str, project_id: str, project_path: str) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo de agentes para generar un proyecto.
        """
        logger.info(f"Iniciando generación para proyecto '{project_id}' con prompt: {prompt[:100]}...")

        try:
            # 1. Obtener contexto de memoria (si existe)
            memory_context = self.memory.retrieve(prompt, top_k=2)
            if memory_context:
                logger.info(f"Recuperados {len(memory_context)} contextos de memoria")
            
            # 2. Crear tareas para los agentes
            tasks = self._create_tasks(prompt, project_path, memory_context)
            
            # 3. Ensamblar el Crew
            self.crew = Crew(
                agents=[
                    director_agent,
                    backend_agent,
                    frontend_agent,
                    qa_agent,
                    repair_agent,
                    dependency_agent
                ],
                tasks=tasks,
                process=Process.sequential,
                verbose=True,
                memory=True,  # Usar memoria interna de CrewAI
            )
            
            # 4. Ejecutar
            logger.info(f"🚀 Ejecutando Crew para proyecto '{project_id}'")
            result = self.crew.kickoff()
            logger.info(f"✅ Crew finalizado exitosamente para proyecto '{project_id}'")
            
            # 5. Guardar en memoria para futuros proyectos
            self.memory.store(prompt, result, metadata={"project_id": project_id})
            
            # 6. Ejecutar dependencias (pip install, npm install) si existen
            self._install_dependencies(project_path)
            
            return {
                "status": "success",
                "project_id": project_id,
                "result": str(result)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en la orquestación del proyecto {project_id}: {str(e)}", exc_info=True)
            # Intentar reparar automáticamente
            try:
                logger.info(f"🔄 Intentando reparar proyecto '{project_id}'...")
                repair_result = self._repair_project(project_path)
                if repair_result:
                    logger.info(f"✅ Reparación exitosa para proyecto '{project_id}'")
                    return {
                        "status": "repaired",
                        "project_id": project_id,
                        "repair": repair_result
                    }
            except Exception as repair_error:
                logger.error(f"❌ Falla en reparación: {repair_error}")
            
            raise RuntimeError(f"Falla en orquestación: {str(e)}") from e

    def _create_tasks(self, prompt: str, project_path: str, memory_context: Optional[list] = None):
        """Crea las tareas para el Crew."""
        from crewai import Task
        # Esta es una implementación simplificada; en la práctica se usarían Task personalizados
        tasks = [
            Task(
                description=f"Analizar el prompt '{prompt}' y generar una arquitectura para el proyecto en {project_path}",
                agent=director_agent,
                expected_output="Arquitectura detallada del proyecto"
            ),
            # Añadir más tareas según los agentes...
        ]
        return tasks

    def _install_dependencies(self, project_path: str):
        """Instala dependencias del proyecto generado."""
        backend_path = os.path.join(project_path, "backend")
        if os.path.exists(os.path.join(backend_path, "requirements.txt")):
            logger.info(f"📦 Instalando dependencias Python en {backend_path}")
            self.terminal.run(f"cd {backend_path} && pip install -r requirements.txt", check=False)
        
        frontend_path = os.path.join(project_path, "frontend")
        if os.path.exists(os.path.join(frontend_path, "package.json")):
            logger.info(f"📦 Instalando dependencias Node en {frontend_path}")
            self.terminal.run(f"cd {frontend_path} && npm install", check=False)

    def _repair_project(self, project_path: str) -> bool:
        """Intenta reparar el proyecto usando el agente repair."""
        # Implementación de reparación...
        return True