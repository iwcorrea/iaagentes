"""
Registro de skills de agentes que escanea recursivamente la carpeta skills/
y normaliza las definiciones usando loaders polimórficos.
"""
from pathlib import Path
from typing import Dict, List, Optional
from core.skill_loader import JsonSkillLoader, YamlSkillLoader, PythonSkillLoader, DirectorySkillLoader


class SkillRegistry:
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir).resolve()
        print(f"🔍 SkillRegistry escaneando {self.skills_dir}")
        self.skills: Dict[str, dict] = {}
        self.skills_by_role: Dict[str, dict] = {}
        self.loaders = [
            DirectorySkillLoader(),
            JsonSkillLoader(),
            YamlSkillLoader(),
            PythonSkillLoader(),
        ]
        self._load_all()

    def _load_all(self):
        if not self.skills_dir.exists():
            print(f"⚠️ Directorio de skills no encontrado: {self.skills_dir}")
            return
        for entry in self.skills_dir.iterdir():
            print(f"  Examinando {entry.name}...")
            skill_data = None
            for loader in self.loaders:
                if loader.can_load(entry):
                    print(f"    -> Probando loader {loader.__class__.__name__}")
                    skill_data = loader.load(entry)
                    if skill_data:
                        break
            if skill_data:
                name = skill_data.get("name")
                role = skill_data.get("role")
                if name:
                    self.skills[name] = skill_data
                if role:
                    self.skills_by_role[role.lower()] = skill_data
                print(f"✅ Skill cargado: {name}")
            else:
                print(f"⚠️ No se pudo cargar skill de {entry}")

    def get_skill_by_name(self, name: str) -> Optional[dict]:
        if name in self.skills:
            return self.skills[name]
        for skill_name, skill in self.skills.items():
            if name in skill_name or skill_name in name:
                return skill
        return None

    def get_skill_by_role(self, role: str) -> Optional[dict]:
        return self.skills_by_role.get(role.lower())

    def list_skills(self) -> List[str]:
        return list(self.skills.keys())