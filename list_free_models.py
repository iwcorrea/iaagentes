# list_free_models.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
resp = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
data = resp.json()

free_models = []
for m in data.get("data", []):
    if ":free" in m["id"]:
        free_models.append(m["id"])

print("✅ Modelos gratuitos disponibles en tu cuenta:")
for mid in sorted(free_models):
    print(" -", mid)