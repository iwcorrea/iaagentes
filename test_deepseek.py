import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# 1. Cargar el entorno local
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL")
model_name = os.getenv("MODEL_PRO")

print("🔄 Conectando a DeepSeek a través del puente autorizado...")
print(f"📡 Canal: {base_url} | Modelo: {model_name}")

try:
    # 2. Inicializar el cliente compatible con OpenRouter
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # 3. Lanzar la petición de prueba
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": "Responde únicamente con la palabra: CONECTADO"}
        ],
        max_tokens=10
    )

    print("\n✅ [PUENTE LIBERADO - CONEXIÓN EXITOSA]:")
    
    # Validar de forma segura si la respuesta es un objeto o un texto plano
    if hasattr(completion, 'choices'):
        print(f"Respuesta de DeepSeek: {completion.choices[0].message.content.strip()}")
    else:
        print(f"Respuesta directa: {str(completion).strip()}")

except Exception as e:
    print(f"\n❌ Ocurrió un inconveniente en la comunicación. Detalles:")
    print(str(e))
