def detect_intent(prompt: str) -> str:
    prompt_lower = prompt.lower()
    
    # Terminal solo si son comandos literales, no descripciones de proyectos
    terminal_triggers = ["pip install", "npm install", "corre el comando", "ejecuta el script"]
    if any(trigger in prompt_lower for trigger in terminal_triggers):
        return "terminal"
    
    # Si el prompt pide explícitamente crear un archivo suelto (sin contexto de proyecto)
    if ("archivo" in prompt_lower and "crea" in prompt_lower) and not any(
        word in prompt_lower for word in [
            "proyecto", "app", "aplicación", "sistema", "web", "api", "backend", "frontend",
            "fullstack", "full-stack", "móvil", "mobile", "landing", "página", "servicio"
        ]
    ):
        return "create_file"
    
    # Todo lo demás (incluyendo descripciones de proyectos) va a los agentes
    return "analysis"