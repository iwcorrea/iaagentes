# start.ps1 - AI-ECOSYSTEM Startup Script
# Mejorado con verificaciones, logs claros y manejo de errores

param(
    [switch]$SkipOllama
)

Write-Host "🚀 Iniciando el ecosistema AI-ECOSYSTEM..." -ForegroundColor Cyan

# 1. Verificar que estamos en el directorio correcto
$projectRoot = $PSScriptRoot
Set-Location $projectRoot

# 2. Activar entorno virtual
Write-Host "📦 Activando entorno virtual..." -ForegroundColor Yellow
if (Test-Path "venv/Scripts/Activate.ps1") {
    & "venv/Scripts/Activate.ps1"
} else {
    Write-Host "❌ No se encontró el entorno virtual. Ejecuta 'python -m venv venv' primero." -ForegroundColor Red
    exit 1
}

# 3. Verificar dependencias
Write-Host "🔍 Verificando dependencias críticas..." -ForegroundColor Yellow
$missing = @()
if (-not (Get-Command uvicorn -ErrorAction SilentlyContinue)) {
    $missing += "uvicorn"
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    $missing += "npm"
}
if ($missing.Count -gt 0) {
    Write-Host "❌ Faltan dependencias: $($missing -join ', '). Ejecuta 'pip install -r requirements.txt' y asegúrate de tener Node.js." -ForegroundColor Red
    exit 1
}

# 4. Preguntar por Ollama (si no se saltó)
if (-not $SkipOllama) {
    $useOllama = Read-Host "¿Iniciar Ollama (modelo local)? (s/n)"
    if ($useOllama -eq 's') {
        Write-Host "🦙 Verificando Ollama..." -ForegroundColor Yellow
        $ollamaRunning = Get-Process -Name ollama -ErrorAction SilentlyContinue
        if (-not $ollamaRunning) {
            Write-Host "🚀 Iniciando Ollama (puede tardar)..." -ForegroundColor Yellow
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 5
        }
        # Verificar que el modelo esté disponible
        $model = (Get-Content -Path "settings.json" | ConvertFrom-Json).llm_model
        if ($model) {
            Write-Host "🦙 Usando modelo local: $model" -ForegroundColor Green
        }
    } else {
        Write-Host "🦙 Ollama no se iniciará (usando solo nube o híbrido si es necesario)." -ForegroundColor Yellow
    }
}

# 5. Iniciar servicios
Write-Host "🔁 Iniciando proxy LiteLLM (puerto 4000)..." -ForegroundColor Cyan
$litellmJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot
    & "venv/Scripts/python" -c "import litellm; litellm.serve(port=4000, config='litellm_config.yaml')"
}
Start-Sleep -Seconds 3
if (-not (Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*4000*" })) {
    Write-Host "⚠️ LiteLLM no responde. Verifica la configuración." -ForegroundColor Yellow
}

Write-Host "🎨 Iniciando Frontend React (puerto 5173)..." -ForegroundColor Cyan
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:projectRoot/nfrontend/frontend"
    npm run dev
}
Start-Sleep -Seconds 3
$frontendRunning = Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*5173*" }
if (-not $frontendRunning) {
    Write-Host "⚠️ El frontend no se inició correctamente." -ForegroundColor Yellow
}

Write-Host "🌐 Iniciando API principal (puerto 8000)..." -ForegroundColor Cyan
$apiJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot
    & "venv/Scripts/uvicorn" api.main:app --reload --port 8000 --host 0.0.0.0
}
Start-Sleep -Seconds 5

# 6. Verificar que la API esté viva
try {
    $apiCheck = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method Head -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($apiCheck.StatusCode -eq 200) {
        Write-Host "✅ API lista en http://localhost:8000/docs" -ForegroundColor Green
    } else {
        Write-Host "⚠️ La API no responde correctamente." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ No se pudo conectar a la API en http://localhost:8000" -ForegroundColor Yellow
}

Write-Host "`n✅ Ecosistema iniciado. Presiona Ctrl+C para detener todos los servicios." -ForegroundColor Green
Write-Host "📋 Accede al dashboard en: http://localhost:5173" -ForegroundColor Cyan

# 7. Mantener el script corriendo
try {
    Wait-Job $litellmJob, $frontendJob, $apiJob
} catch {
    Write-Host "`n🛑 Deteniendo servicios..." -ForegroundColor Red
    Stop-Job $litellmJob, $frontendJob, $apiJob
    Remove-Job $litellmJob, $frontendJob, $apiJob
    Write-Host "✅ Ecosistema detenido." -ForegroundColor Green
}