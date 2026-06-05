# test_crewai.py
import os
from workflows.ecommerce_workflow import run_ecommerce_workflow

if __name__ == "__main__":
    prompt = "Crea un backend de ecommerce con FastAPI"
    print("Probando run_ecommerce_workflow...")
    try:
        result = run_ecommerce_workflow(prompt)
        print("Resultado:")
        print(result)
    except Exception as e:
        print(f"ERROR: {e}")