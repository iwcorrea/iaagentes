# start.ps1
$ErrorActionPreference = "Stop"

Write-Host "🚀 Iniciando el ecosistema AI-ECOSYSTEM..."
Write-Host "📦 Activando entorno virtual..."
& ".\venv\Scripts\Activate.ps1"

# Preguntar si se inicia Ollama
$ollamaChoice = Read-Host "¿Iniciar Ollama (modelo local)? (s/n)"
if ($ollamaChoice -eq "s") {
    Write-Host "🦙 Iniciando Ollama..."
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
} else {
    Write-Host "🦙 Ollama no se iniciará."
}

# Establecer raíz del proyecto para el backend
$env:AI_ECOSYSTEM_ROOT = (Get-Location).Path
Write-Host "📂 Raíz del proyecto: $env:AI_ECOSYSTEM_ROOT"

# Iniciar proxy LiteLLM
Write-Host "🔁 Iniciando proxy LiteLLM (puerto 4000)..."
Start-Process "litellm" -ArgumentList "--config litellm_config.yaml" -WindowStyle Minimized

# Iniciar frontend React con npm usando cmd.exe (evita ambigüedad de PowerShell)
Write-Host "🎨 Iniciando Frontend React (puerto 5173)..."
$frontendDir = Join-Path (Get-Location) "nfrontend\frontend"
Start-Process "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory $frontendDir -WindowStyle Minimized

# Iniciar API principal
Write-Host "🌐 Iniciando API principal (puerto 8000)..."
uvicorn api.main:app --reload --port 8000 --host 127.0.0.1

Write-Host "✅ Ecosistema detenido."