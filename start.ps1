# start.ps1
# Script de arranque del ecosistema AI-ECOSYSTEM

Write-Host "🚀 Iniciando el ecosistema AI-ECOSYSTEM..." -ForegroundColor Cyan

# Activar entorno virtual
Write-Host "📦 Activando entorno virtual..." -ForegroundColor Yellow
.\venv\Scripts\activate

# Iniciar LiteLLM en segundo plano
Write-Host "🔁 Iniciando proxy LiteLLM (puerto 4000)..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "litellm" -ArgumentList "--config litellm_config.yaml --port 4000"

# Esperar a que LiteLLM esté listo
Write-Host "⏳ Esperando a que LiteLLM esté listo..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Iniciar la API principal
Write-Host "🌐 Iniciando API principal (puerto 8000)..." -ForegroundColor Yellow
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

Write-Host "✅ Ecosistema iniciado correctamente." -ForegroundColor Green
Write-Host "   LiteLLM: http://localhost:4000" -ForegroundColor Cyan
Write-Host "   API:     http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Docs:    http://localhost:8000/docs" -ForegroundColor Cyan