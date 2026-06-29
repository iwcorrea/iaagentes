import os
import json
import re
import tempfile
from pathlib import Path
from typing import Dict, Any, List

from crewai import Agent, Task, Crew
from core.agent_cache import AgentCache
from core.project_memory import ProjectMemory
from core.skill_registry import SkillRegistry
from tools.jenngen_tool import run_jenngen


class PhaseGenerator:
    def __init__(self, workspace_path: Path, agent_cache: AgentCache, memory: ProjectMemory):
        self.workspace_path = workspace_path
        self.agent_cache = agent_cache
        self.memory = memory
        self.skill_registry = SkillRegistry()

    def execute(self, user_prompt: str) -> Dict[str, Any]:
        context = self.memory.get_manifest_summary()
        design = self.memory.get_design_context()
        full_context = f"{context}\n{design}" if design else context

        director_instructions = self.memory.get_instructions_for_agent("director")
        backend_instructions = self.memory.get_instructions_for_agent("backend")
        frontend_instructions = self.memory.get_instructions_for_agent("frontend")

        director_prompt = user_prompt
        if director_instructions:
            director_prompt = f"{director_instructions}\n\n🔧 TAREA: {user_prompt}"
        if full_context and "vacío" not in full_context:
            director_prompt += f"\n\n{full_context}\nBasate en los archivos existentes. No dupliques."

        # --- DETECCIÓN DE ARCHIVO ÚNICO EXPLÍCITO ---
        single_file_match = re.search(r"Creá\s+UN\s+SOLO\s+archivo\s+llamado\s+([\w\-]+\.\w+)", user_prompt, re.IGNORECASE)
        forced_single_file = single_file_match.group(1) if single_file_match else None

        if forced_single_file:
            plan = [{"path": forced_single_file, "purpose": "Archivo único solicitado"}]
            design_notes = []
            print(f"📌 Plan forzado a un solo archivo: {forced_single_file}")
        else:
            director = self.agent_cache.get_or_create("director", lambda: Agent(
                role="Arquitecto de Software",
                goal="Planificar la estructura de archivos necesaria para implementar el requerimiento del usuario.",
                backstory="Eres un arquitecto senior experto en diseño de aplicaciones web con FastAPI y React.",
                verbose=True, allow_delegation=False
            ))

            plan_task = Task(description=(
                f"Analiza el siguiente requerimiento y genera un plan de archivos JSON.\n"
                f"Requerimiento:\n{director_prompt}\n\n"
                "IMPORTANTE: Si solo se necesita un archivo, el plan debe tener un solo elemento con ese path.\n"
                "Todas las rutas deben ser relativas, sin barras al inicio (ej: 'styles.css', NO '/styles.css').\n"
                "No repitas el mismo path más de una vez.\n"
                "Responde EXCLUSIVAMENTE con un JSON válido con esta estructura:\n"
                '{"plan": [{"path": "ruta/archivo.ext", "purpose": "descripción breve"}], '
                '"design_notes": ["lista de decisiones de diseño importantes"]}\n'
                "No incluyas ningún texto fuera del JSON."
            ), agent=director, expected_output="JSON con el plan de archivos.")

            crew_plan = Crew(agents=[director], tasks=[plan_task], verbose=True)
            crew_plan.kickoff()
            plan_raw = self._get_raw_output(plan_task.output)
            print("📋 Plan de generación:", plan_raw[:300])

            plan_data = self._extract_plan(plan_raw, user_prompt)
            plan = plan_data.get("plan", [])
            design_notes = plan_data.get("design_notes", [])

            # Inyectar archivos explícitos del prompt
            explicit_files = re.findall(r'\b([\w\-/]+\.(?:css|js|html|py|txt|md|json|yaml|yml))\b', user_prompt)
            explicit_basenames = {Path(f).name for f in explicit_files}
            existing_paths = {item["path"] for item in plan}
            for fname in explicit_basenames:
                if fname not in existing_paths:
                    plan.append({"path": fname, "purpose": "Archivo solicitado en el prompt"})
                    print(f"📌 Archivo inyectado en el plan: {fname}")

            if not plan:
                print("❌ No se pudo extraer el plan. Abortando.")
                return {"files": {}}

        # Deduplicar y sanitizar
        seen = set()
        unique_plan = []
        for item in plan:
            path = item.get("path", "")
            if path not in seen:
                seen.add(path)
                unique_plan.append(item)
        plan = unique_plan

        # --- DETECCIÓN DE PROYECTO FRONTEND PURO ---
        has_backend = any(f["path"].endswith((".py", ".txt")) for f in plan)
        is_frontend_only = not has_backend and any(f["path"].endswith((".html", ".css", ".js", ".jsx", ".tsx")) for f in plan)

        for item in plan:
            original = item["path"]
            item["path"] = self._sanitize_path(original, force_flat=is_frontend_only)

        for note in design_notes if not forced_single_file else []:
            self.memory.add_design_decision(note)

        # Forzar regeneración de archivos mencionados en el prompt
        force_files = {item["path"] for item in plan if item["path"] in user_prompt}

        new_files = []
        for f in plan:
            if forced_single_file and f["path"] == forced_single_file:
                new_files.append(f)
            elif f["path"] in force_files or not self.memory.file_exists(f["path"]):
                new_files.append(f)

        print(f"📁 Archivos nuevos a generar: {len(new_files)} (ya existían {len(plan) - len(new_files)})")

        if not new_files:
            print("✅ Todos los archivos ya existen. Nada que generar.")
            return {"files": {}}

        backend_files = [f for f in new_files if f["path"].endswith((".py", ".txt"))]
        frontend_files = [f for f in new_files if f["path"].endswith((".jsx", ".tsx", ".css", ".json", ".js", ".html", ".md"))]
        other_files = [f for f in new_files if f not in backend_files and f not in frontend_files]

        files = {}

        backend_agent = self._create_agent_with_instructions("backend", backend_instructions,
            role="Desarrollador Backend Python",
            goal="Generar código Python/FastAPI de alta calidad.",
            backstory="Eres un desarrollador backend experto en FastAPI."
        )
        if backend_files:
            files.update(self._generate_code_for_files(backend_files, backend_agent, "Backend"))

        if frontend_files:
            # Buscar skill especializado para landing pages
            landing_skill = self.skill_registry.get_skill_by_name("landing-builder")
            if landing_skill and ("landing" in user_prompt.lower() or "frontend" in user_prompt.lower()):
                frontend_agent = self.agent_cache.get_or_create("landing-builder", lambda: Agent(
                    role=landing_skill["role"],
                    goal=landing_skill["goal"],
                    backstory=landing_skill["backstory"],
                    verbose=True, allow_delegation=False
                ))
                files.update(self._generate_code_for_files(frontend_files, frontend_agent, "Frontend"))
            elif self.skill_registry.get_skill_by_name("jenngen"):
                files.update(self._generate_frontend_with_jenngen(frontend_files, frontend_instructions))
            else:
                frontend_agent = self._create_agent_with_instructions("frontend", frontend_instructions,
                    role="Desarrollador Frontend React",
                    goal="Generar componentes React con Tailwind CSS.",
                    backstory="Eres un desarrollador frontend experto en React y Tailwind."
                )
                files.update(self._generate_code_for_files(frontend_files, frontend_agent, "Frontend"))

        if other_files:
            generic_agent = self.agent_cache.get_or_create("generic", lambda: Agent(
                role="Generador de archivos",
                goal="Generar el contenido solicitado para cualquier tipo de archivo.",
                backstory="Eres un asistente que genera archivos de configuración, documentación, etc.",
                verbose=True, allow_delegation=False
            ))
            files.update(self._generate_code_for_files(other_files, generic_agent, "Otros"))

        sanitized_files = {self._sanitize_path(k, force_flat=is_frontend_only): v for k, v in files.items()}
        if not sanitized_files:
            print("❌ No se generaron archivos.")
            return {"files": {}}

        valid_files = {}
        for fpath, content in sanitized_files.items():
            if fpath.endswith(".py") and not self._is_valid_python(content):
                print(f"⚠️ Archivo Python con errores sintácticos descartado: {fpath}")
            else:
                valid_files[fpath] = content

        print(f"✅ Generados {len(valid_files)} archivos en total.")
        return {"files": valid_files}

    # ─── helpers ───

    def _sanitize_path(self, path: str, force_flat: bool = False) -> str:
        clean = path.strip()
        if clean.startswith('./'):
            clean = clean[2:]
        elif clean.startswith('.\\'):
            clean = clean[2:]
        clean = clean.lstrip("/\\")
        if ":" in clean:
            clean = clean.split(":", 1)[-1].lstrip("\\/")
        # Si es un proyecto frontend puro, quitar prefijos como "src/" o "public/"
        if force_flat:
            # Tomar solo el nombre del archivo, ignorando carpetas
            clean = Path(clean).name
        return clean

    def _get_raw_output(self, task_output) -> str:
        return task_output.raw if hasattr(task_output, 'raw') else str(task_output)

    def _extract_plan(self, raw: str, fallback_prompt: str = "") -> dict:
        data = self._extract_json_from_text(raw)
        if isinstance(data, dict):
            if "plan" in data:
                return data
            keys = [k for k in data if k != "design_notes"]
            if len(keys) == 1 and "." in keys[0]:
                val = data[keys[0]]
                if isinstance(val, dict) and "path" in val:
                    return {"plan": [{"path": val["path"], "purpose": val.get("purpose", "")}], "design_notes": data.get("design_notes", [])}
                if isinstance(val, str):
                    return {"plan": [{"path": keys[0], "purpose": "Archivo solicitado"}], "design_notes": data.get("design_notes", [])}
            file_keys = [k for k in keys if "." in k]
            if file_keys:
                return {"plan": [{"path": k, "purpose": "Archivo"} for k in file_keys], "design_notes": data.get("design_notes", [])}
        if fallback_prompt:
            matches = re.findall(r'\b([\w\-/]+\.\w+)\b', fallback_prompt)
            if matches:
                file_matches = [m for m in matches if not m.startswith("frontend-design")]
                if file_matches:
                    return {"plan": [{"path": m.split("/")[-1], "purpose": "Archivo deducido"} for m in file_matches], "design_notes": []}
        return {}

    def _create_agent_with_instructions(self, agent_name: str, instructions: str, **kwargs):
        if instructions:
            kwargs["backstory"] = f"{kwargs.get('backstory', '')}\n\n📚 Sigue estas instrucciones:\n{instructions}"
        return self.agent_cache.get_or_create(agent_name, lambda: Agent(**kwargs, verbose=True, allow_delegation=False))

    def _generate_code_for_files(self, file_entries: list, agent: Agent, category: str) -> Dict[str, str]:
        expected_keys = [f["path"] for f in file_entries]
        file_list = "\n".join([f"- {f['path']}: {f['purpose']}" for f in file_entries])
        task_desc = (
            f"Genera el código completo para los siguientes archivos {category}.\n{file_list}\n\n"
            f"Los archivos esperados son exactamente: {', '.join(expected_keys)}.\n"
            "Responde EXCLUSIVAMENTE con un JSON donde las claves sean las rutas y los valores el código fuente.\n"
            "Ejemplo: {\"script.js\": \"console.log('hola');\"}\n"
            "No uses backticks alrededor del JSON, solo el objeto JSON puro."
        )
        task = Task(description=task_desc, agent=agent, expected_output="JSON con archivos generados.")
        for attempt in range(1, 4):
            try:
                crew = Crew(agents=[agent], tasks=[task], verbose=True)
                crew.kickoff()
                raw = self._get_raw_output(task.output)
                files = self._robust_extract_files(raw, expected_keys)
                if files:
                    return {self._sanitize_path(k): str(v) if not isinstance(v, str) else v for k, v in files.items()}
                print(f"⚠️ Intento {attempt}: extracción fallida. Reintentando...")
            except Exception as e:
                print(f"❌ Intento {attempt} error: {e}")
        return {}

    def _robust_extract_files(self, raw_text: str, expected_keys: List[str] = None) -> Dict[str, str]:
        raw = raw_text.strip()

        # 1. JSON puro o balanceado
        data = self._extract_json_from_text(raw)
        if isinstance(data, dict) and any('/' in k or '\\' in k for k in data):
            return data

        # 2. Bloque ```json ... ```
        m = re.search(r'```json\s*\n(.*?)\n```', raw, re.DOTALL)
        if m:
            inner = self._extract_json_from_text(m.group(1))
            if isinstance(inner, dict):
                return inner

        # 3. Reparar backticks/comillas
        for candidate in self._repair_json(raw):
            data = self._extract_json_from_text(candidate)
            if isinstance(data, dict):
                return data

        # 4. Si se espera un único archivo, usar todo el texto como contenido
        if expected_keys and len(expected_keys) == 1:
            return {expected_keys[0]: raw}

        # 5. Buscar bloques de código con nombre de archivo
        code_blocks = re.findall(r'```(?:\w+)?[:\s]+([\w\-./\\]+\.\w+)\s*\n(.*?)```', raw, re.DOTALL)
        if code_blocks:
            files = {}
            for fname, code in code_blocks:
                clean_name = self._sanitize_path(fname)
                files[clean_name] = code.strip()
            if files:
                return files

        # 6. Patrón ruta:::código
        files = {}
        pattern = re.findall(r'["\']?([\w\-./\\]+\.\w+)["\']?\s*:::\s*(.*?)(?=\n\S+:::\s|\Z)', raw, re.DOTALL)
        for path, code in pattern:
            files[self._sanitize_path(path.strip())] = code.strip()
        return files

    def _repair_json(self, text: str) -> List[str]:
        candidates = []
        t = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip(), flags=re.MULTILINE)
        candidates.append(t)
        candidates.append(t.replace('`', '"'))
        candidates.append(t.replace("'", '"'))
        try:
            json.loads(t)
        except:
            fixed = re.sub(r',\s*}', '}', t)
            fixed = re.sub(r',\s*]', ']', fixed)
            candidates.append(fixed)
        return candidates

    @staticmethod
    def _extract_json_from_text(text: str) -> Any:
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
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                try:
                    return json.loads(text[start:end].replace('\n', '\\n'))
                except:
                    pass
        return None

    @staticmethod
    def _is_valid_python(code: str) -> bool:
        try:
            compile(code, '<generated>', 'exec')
            return True
        except SyntaxError:
            return False

    def _generate_frontend_with_jenngen(self, file_entries: list, instructions: str) -> Dict[str, str]:
        print("🧠 Usando JennGen para mejorar el frontend...")
        pseudo_agent = self._create_agent_with_instructions("frontend", instructions,
            role="Redactor de pseudocódigo",
            goal="Escribir pseudocódigo detallado para componentes frontend.",
            backstory="Describís componentes web usando lenguaje natural y etiquetas simplificadas."
        )
        expected_keys = [f["path"] for f in file_entries]
        file_list = "\n".join([f"- {f['path']}: {f['purpose']}" for f in file_entries])
        task_desc = (
            f"Escribí el pseudocódigo para los siguientes archivos frontend.\n{file_list}\n\n"
            "Usá un formato simplificado pero claro. Para HTML usá etiquetas normales, "
            "para CSS usá reglas breves, para JSX describí la estructura con componentes y props.\n"
            "El valor de cada archivo debe ser un string con el código o pseudocódigo, NO un objeto JSON.\n"
            "Respondé EXCLUSIVAMENTE con un JSON válido (sin markdown) donde las claves son las rutas "
            "y los valores strings de pseudocódigo."
        )
        task = Task(description=task_desc, agent=pseudo_agent, expected_output="JSON con pseudocódigo (sin markdown).")
        crew = Crew(agents=[pseudo_agent], tasks=[task], verbose=True)
        crew.kickoff()
        raw_output = self._get_raw_output(task.output)
        pseudo_files = self._robust_extract_files(raw_output, expected_keys)
        if not pseudo_files and expected_keys:
            pseudo_files = {expected_keys[0]: raw_output}
            print(f"⚠️ No se pudo extraer JSON. Usando raw completo para {expected_keys[0]}.")
        cleaned = {}
        for fpath, val in pseudo_files.items():
            clean = self._sanitize_path(fpath)
            if isinstance(val, dict):
                cleaned[clean] = val.get("Contenido", json.dumps(val, ensure_ascii=False))
            elif not isinstance(val, str):
                cleaned[clean] = str(val)
            else:
                cleaned[clean] = val
        if not cleaned:
            print("⚠️ No se generó pseudocódigo. Usando generación normal.")
            frontend_agent = self._create_agent_with_instructions("frontend", instructions,
                role="Desarrollador Frontend React",
                goal="Generar componentes React con Tailwind CSS.",
                backstory="Eres un desarrollador frontend experto en React y Tailwind."
            )
            return self._generate_code_for_files(file_entries, frontend_agent, "Frontend")
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            for fpath, content in cleaned.items():
                dest = tmp / fpath
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(str(content), encoding='utf-8')
            try:
                model = os.environ.get("CURRENT_BRAIN_MODEL", "local-coder")
                ollama_model = "qwen2.5-coder:1.5b" if model == "local-coder" else None
                generated = run_jenngen(str(tmp), model=ollama_model)
                clean_generated = {}
                for k, v in generated.items():
                    clean_key = self._sanitize_path(k.replace("src/", "").replace("frontend/", ""))
                    clean_generated[clean_key] = v
                return clean_generated or {}
            except Exception as e:
                print(f"❌ Falló JennGen: {e}. Usando generación normal.")
                frontend_agent = self._create_agent_with_instructions("frontend", instructions,
                    role="Desarrollador Frontend React",
                    goal="Generar componentes React con Tailwind CSS.",
                    backstory="Eres un desarrollador frontend experto en React y Tailwind."
                )
                return self._generate_code_for_files(file_entries, frontend_agent, "Frontend")