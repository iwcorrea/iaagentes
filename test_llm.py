from agents.director_agent import director_agent

try:
    response = director_agent.kickoff("Di 'Hola' solamente.")
    print("✅ Respuesta del agente:", response)
except Exception as e:
    print("❌ Error:", e)