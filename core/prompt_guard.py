MAX_PROMPT_CHARS = 3000
MAX_ESTIMATED_TOKENS = 1500

def validate_prompt(prompt: str) -> dict:
    """Valida y optimiza un prompt antes de enviarlo a los agentes."""
    result = {
        "valid": True,
        "reason": "",
        "optimized_prompt": prompt,
        "estimated_tokens": 0,
    }

    # 1. Longitud excesiva
    if len(prompt) > MAX_PROMPT_CHARS:
        result["valid"] = False
        result["reason"] = (
            f"El prompt es demasiado largo ({len(prompt)} caracteres, máximo {MAX_PROMPT_CHARS}). "
            "Dividilo en prompts más pequeños o usá el asistente guiado."
        )
        return result

    # 2. Estimación de tokens (aproximado: 1 token ≈ 4 caracteres)
    estimated = len(prompt) // 4
    result["estimated_tokens"] = estimated

    if estimated > MAX_ESTIMATED_TOKENS:
        # Optimizar: eliminar líneas vacías y espacios extra
        optimized = "\n".join(line.strip() for line in prompt.splitlines() if line.strip())
        result["optimized_prompt"] = optimized
        result["estimated_tokens"] = len(optimized) // 4

        if result["estimated_tokens"] > MAX_ESTIMATED_TOKENS:
            result["valid"] = False
            result["reason"] = (
                f"El prompt es demasiado largo (~{estimated} tokens estimados, máximo {MAX_ESTIMATED_TOKENS}). "
                "Reducí la cantidad de requisitos o usá el asistente guiado."
            )
            return result

    # 3. Palabras clave mínimas para orientar a los agentes
    keywords = ["backend", "frontend", "react", "fastapi", "api", "web", "móvil", "mobile"]
    has_keywords = any(kw in prompt.lower() for kw in keywords)
    if not has_keywords:
        result["reason"] = (
            "El prompt no especifica el tipo de proyecto (backend, frontend, web, móvil). "
            "Agregá palabras clave para orientar a los agentes."
        )
        result["valid"] = False

    return result