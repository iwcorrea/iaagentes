from dotenv import load_dotenv
import os

load_dotenv()

print("KEY:")
print(os.getenv("OPENAI_API_KEY"))

print("\nBASE URL:")
print(os.getenv("OPENAI_BASE_URL"))

print("\nMODEL:")
print(os.getenv("MODEL_PRO"))