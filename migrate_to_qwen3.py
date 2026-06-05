import os

agents_dir = "agents"
new_model_line = '    model="openrouter/qwen/qwen3-coder:free",\n'

files_to_update = [
    "director_agent.py",
    "backend_agent.py",
    "frontend_agent.py",
    "qa_agent.py",
    "repair_agent.py"
]

for filename in files_to_update:
    filepath = os.path.join(agents_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith('model="openrouter/'):
            new_lines.append(new_model_line)
        else:
            new_lines.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"✅ {filename} actualizado a qwen/qwen3-coder:free")

print("Migración completada. Todos los agentes usan ahora Qwen3 Coder gratuito.")