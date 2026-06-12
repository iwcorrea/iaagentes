# ============================================================
# AI-ECOSYSTEM – Arranque centralizado (modo pruebas)
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

# 2. Iniciar LiteLLM en segundo plano
Write-Host "🔁 Iniciando proxy LiteLLM (puerto 4000)..." -ForegroundColor Yellow
$litellmLog = Join-Path (Get-Location) "logs\litellm.log"
New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null
$litellmJob = Start-Job -Name "LiteLLM" -ScriptBlock {
    param($logFile)
    & litellm --config litellm_config.yaml --port 4000 *>> $logFile
} -ArgumentList $litellmLog

# 3. Iniciar Frontend React en segundo plano
Write-Host "🎨 Iniciando Frontend React (puerto 5173)..." -ForegroundColor Yellow
$frontendPath = Join-Path (Get-Location) "nfrontend\frontend"
if (-not (Test-Path "$frontendPath\package.json")) {
    Write-Host "⚠️ No se encontró package.json en $frontendPath. Omitiendo frontend." -ForegroundColor DarkYellow
} else {
    $frontendLog = Join-Path (Get-Location) "logs\frontend.log"
    $frontendJob = Start-Job -Name "FrontendReact" -ScriptBlock {
        param($path, $logFile)
        Set-Location $path
        if (-not (Test-Path "node_modules")) {
            Write-Host "📦 Instalando dependencias del frontend..." *>> $logFile
            npm install *>> $logFile
        }
        npm run dev *>> $logFile
    } -ArgumentList $frontendPath, $frontendLog
}

# 4. Esperar a que LiteLLM esté listo
Write-Host "⏳ Esperando a que LiteLLM esté listo..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:4000/v1/models" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $ready = $true
            Write-Host "✅ LiteLLM listo en http://localhost:4000" -ForegroundColor Green
            break
        }
    } catch { }
}
if (-not $ready) {
    Write-Host "⚠️ LiteLLM tardó demasiado o falló. Revisá logs/litellm.log" -ForegroundColor DarkYellow
}

# 5. Iniciar API principal (SIN --reload para evitar reinicios)
Write-Host "🌐 Iniciando API principal (puerto 8000)..." -ForegroundColor Yellow
try {
    uvicorn api.main:app --host 0.0.0.0 --port 8000
} catch {
    Write-Host "❌ Error al iniciar la API." -ForegroundColor Red
} finally {
    if ($litellmJob) {
        Stop-Job -Name "LiteLLM" -ErrorAction SilentlyContinue
        Remove-Job -Name "LiteLLM" -ErrorAction SilentlyContinue
        Write-Host "🛑 LiteLLM detenido." -ForegroundColor Gray
    }
    if ($frontendJob) {
        Stop-Job -Name "FrontendReact" -ErrorAction SilentlyContinue
        Remove-Job -Name "FrontendReact" -ErrorAction SilentlyContinue
        Write-Host "🛑 Frontend React detenido." -ForegroundColor Gray
    }
}

Write-Host "✅ Ecosistema detenido." -ForegroundColor Cyan