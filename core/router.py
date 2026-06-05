def detect_intent(prompt: str) -> str:
    prompt_lower = prompt.lower()
    if any(word in prompt_lower for word in ["ejecuta", "instala", "pip install", "npm install"]):
        return "terminal"
    if any(word in prompt_lower for word in [
        "proyecto", "backend", "sistema", "app", "api",
        "web", "frontend", "aplicación", "ecommerce", "tienda",
        "inventario", "reservas", "hotel", "blog", "cms",
        "microservicio", "rest", "graphql", "fastapi", "django"
    ]):
        return "analysis"
    if ("archivo" in prompt_lower and "crea" in prompt_lower) or \
       any(ext in prompt_lower for ext in [".py", ".js", ".jsx", ".ts"]):
        return "create_file"
    return "analysis" # Fallback seguro para proyectos
