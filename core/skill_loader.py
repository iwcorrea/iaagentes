"""
Loaders polimórficos para skills de agentes desde múltiples formatos.
Soporta JSON, YAML, Python y directorios con manifiesto.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Optional, Any
from importlib import util as importlib_util

import yaml


class SkillLoader:
    def can_load(self, path: Path) -> bool:
        raise NotImplementedError

    def load(self, path: Path) -> Optional[Dict[str, Any]]:
        raise NotImplementedError


class JsonSkillLoader(SkillLoader):
    def can_load(self, path: Path) -> bool:
        return path.suffix == '.json'

    def load(self, path: Path) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or "name" not in data:
                print(f"⚠️ Skill JSON inválido (falta 'name'): {path}")
                return None
            return self._normalize(data)
        except json.JSONDecodeError as e:
            print(f"❌ Error de JSON en {path}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error inesperado cargando {path}: {e}")
            return None

    def _normalize(self, data: dict) -> dict:
        return {
            "name": data.get("name", ""),
            "role": data.get("role", ""),
            "goal": data.get("goal", ""),
            "backstory": data.get("backstory", ""),
            "tools": data.get("tools", []),
            "verbose": data.get("verbose", True),
            "allow_delegation": data.get("allow_delegation", False),
            "model_preference": data.get("model_preference", ""),
            "tags": data.get("tags", []),
            "prompts": data.get("prompts", {}),
            "context_files": data.get("context_files", []),
        }


class YamlSkillLoader(SkillLoader):
    def can_load(self, path: Path) -> bool:
        return path.suffix in ('.yaml', '.yml')

    def load(self, path: Path) -> Optional[Dict[str, Any]]:
        try:
            data = yaml.safe_load(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or "name" not in data:
                print(f"⚠️ Skill YAML inválido (falta 'name'): {path}")
                return None
            return self._normalize(data)
        except Exception as e:
            print(f"❌ Error cargando YAML {path}: {e}")
            return None

    def _normalize(self, data: dict) -> dict:
        return {
            "name": data.get("name", ""),
            "role": data.get("role", ""),
            "goal": data.get("goal", ""),
            "backstory": data.get("backstory", ""),
            "tools": data.get("tools", []),
            "verbose": data.get("verbose", True),
            "allow_delegation": data.get("allow_delegation", False),
            "model_preference": data.get("model_preference", ""),
            "tags": data.get("tags", []),
            "prompts": data.get("prompts", {}),
            "context_files": data.get("context_files", []),
        }


class PythonSkillLoader(SkillLoader):
    def can_load(self, path: Path) -> bool:
        return path.suffix == '.py'

    def load(self, path: Path) -> Optional[Dict[str, Any]]:
        try:
            spec = importlib_util.spec_from_file_location("skill_module", path)
            module = importlib_util.module_from_spec(spec)
            sys.modules["skill_module"] = module
            spec.loader.exec_module(module)
            if hasattr(module, "get_skill_config"):
                return module.get_skill_config()
            return None
        except Exception as e:
            print(f"❌ Error cargando skill Python {path}: {e}")
            return None


class DirectorySkillLoader(SkillLoader):
    MANIFEST_NAMES = ["manifest.yaml", "manifest.json", "skill.yaml", "skill.json", "agent.yaml", "agent.json"]

    def can_load(self, path: Path) -> bool:
        return path.is_dir()

    def load(self, path: Path) -> Optional[Dict[str, Any]]:
        for name in self.MANIFEST_NAMES:
            manifest = path / name
            if manifest.exists():
                loader = self._get_loader_for(manifest)
                if loader:
                    return loader.load(manifest)
        return self._load_from_parts(path)

    def _get_loader_for(self, file_path: Path):
        if file_path.suffix == '.json':
            return JsonSkillLoader()
        elif file_path.suffix in ('.yaml', '.yml'):
            return YamlSkillLoader()
        return None

    def _load_from_parts(self, path: Path) -> Optional[Dict[str, Any]]:
        config = {
            "name": path.name,
            "role": "",
            "goal": "",
            "backstory": "",
            "tools": [],
            "verbose": True,
            "allow_delegation": False,
            "model_preference": "",
            "tags": [],
            "prompts": {},
            "context_files": [],
        }
        prompt_file = path / "system_prompt.md"
        if prompt_file.exists():
            config["backstory"] = prompt_file.read_text(encoding='utf-8')
        tools_dir = path / "tools"
        if tools_dir.exists():
            for tool_file in tools_dir.glob("*.py"):
                config["tools"].append(tool_file.stem)
        return config if config["backstory"] or config["tools"] else None