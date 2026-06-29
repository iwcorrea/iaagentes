"""
Herramienta que transforma pseudocódigo en código real usando LiteLLM,
emulando el comportamiento de JennGen pero integrado en nuestro ecosistema.
"""
import os
from pathlib import Path
from typing import Dict, Optional

def _call_litellm(prompt: str, model: str = None) -> str:
    """Envía un prompt a LiteLLM y devuelve la respuesta."""
    import litellm
    if not model:
        model = os.environ.get("CURRENT_BRAIN_MODEL", "local-coder")
    model_map = {
        "local-coder": "ollama/qwen2.5-coder:1.5b",
        "cloud-coder": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    }
    real_model = model_map.get(model, model)
    try:
        response = litellm.completion(
            model=real_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=4096
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"LiteLLM call failed: {str(e)}")

def run_jenngen(
    source_folder: str,
    output_folder: Optional[str] = None,
    model: Optional[str] = None,
    instructions_file: Optional[str] = None
) -> Dict[str, str]:
    """
    Toma archivos de pseudocódigo de source_folder, los envía a LiteLLM
    para que los complete/mejore, y devuelve el código generado.
    """
    source = Path(source_folder).resolve()
    if not source.exists():
        raise FileNotFoundError(f"Source folder not found: {source}")

    generated_files = {}
    for file_path in source.glob("*"):
        if not file_path.is_file():
            continue
        original_content = file_path.read_text(encoding="utf-8", errors="replace")
        prompt = (
            f"You are a code generator. Convert the following pseudocode into fully functional, "
            f"clean, and professional code. Keep the same file type and structure.\n\n"
            f"Pseudocode for {file_path.name}:\n{original_content}\n\n"
            f"Respond ONLY with the final code, no explanations."
        )
        try:
            improved_code = _call_litellm(prompt, model=model)
            generated_files[file_path.name] = improved_code
        except Exception as e:
            print(f"⚠️ LiteLLM falló para {file_path.name}: {e}")
            generated_files[file_path.name] = original_content

    return generated_files