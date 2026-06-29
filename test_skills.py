from core.skill_registry import SkillRegistry
reg = SkillRegistry()
print("Skills cargados:", list(reg.skills.keys()))
print("Skills por rol:", list(reg.skills_by_role.keys()))