# ============================================================
# AI-ECOSYSTEM – Arranque centralizado (con Ollama local)
# ============================================================
Write-Host "🚀 Iniciando el ecosistema AI-ECOSYSTEM..." -ForegroundColor Cyan

# 1. Activar entorno virtual
$venvPath = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "📦 Activando entorno virtual..." -ForegroundColor Yellow
    . $venvPath
} else {
    Write-Host "❌ No se encontró el entorno virtual en $venvPath" -ForegroundColor Red
    exit 1
}

# 2. Iniciar Ollama si no está corriendo
Write-Host "🦙 Verificando Ollama..." -ForegroundColor Yellow
$ollamaRunning = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if (-not $ollamaRunning) {
    Write-Host "🦙 Iniciando Ollama (modelo local)..." -ForegroundColor Yellow
    Start-Process -NoNewWindow -FilePath "ollama" -ArgumentList "serve"
    Start-Sleep -Seconds 3
    Write-Host "✅ Ollama iniciado." -ForegroundColor Green
} else {
    Write-Host "✅ Ollama ya está corriendo." -ForegroundColor Green
}

# 3. Iniciar LiteLLM en segundo plano
Write-Host "🔁 Iniciando proxy LiteLLM (puerto 4000)..." -ForegroundColor Yellow
$litellmLog = ".\logs\litellm.log"
New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null
$litellmJob = Start-Job -Name "LiteLLM" -ScriptBlock {
    param($logFile)
    & litellm --config litellm_config.yaml --port 4000 *>> $logFile
} -ArgumentList $litellmLog

# 4. Iniciar Frontend React en segundo plano
Write-Host "🎨 Iniciando Frontend React (puerto 5173)..." -ForegroundColor Yellow
$frontendPath = ".\nfrontend\frontend"
if (Test-Path "$frontendPath\package.json") {
    $frontendLog = ".\logs\frontend.log"
    $frontendJob = Start-Job -Name "FrontendReact" -ScriptBlock {
        param($path, $logFile)
        Set-Location $path
        if (-not (Test-Path "node_modules")) {
            Write-Host "📦 Instalando dependencias del frontend..." *>> $logFile
            npm install *>> $logFile
        }
        npm run dev *>> $logFile
    } -ArgumentList (Resolve-Path $frontendPath).Path, (Join-Path (Get-Location) "logs\frontend.log")
}

# 5. Iniciar API principal
Write-Host "🌐 Iniciando API principal (puerto 8000)..." -ForegroundColor Yellow
try {
    uvicorn api.main:app --host 0.0.0.0 --port 8000
} catch {
    Write-Host "❌ Error al iniciar la API." -ForegroundColor Red
} finally {
    if ($litellmJob) {
        Stop-Job -Name "LiteLLM" -ErrorAction SilentlyContinue
        Remove-Job -Name "LiteLLM" -ErrorAction SilentlyContinue
    }
    if ($frontendJob) {
        Stop-Job -Name "FrontendReact" -ErrorAction SilentlyContinue
        Remove-Job -Name "FrontendReact" -ErrorAction SilentlyContinue
    }
}

Write-Host "✅ Ecosistema detenido." -ForegroundColor Cyan