# ============================================================
# APLICACIÓN DE COBROS – Arranque unificado
# ============================================================
Clear-Host
Write-Host "🚀 Iniciando Aplicación de Cobros..." -ForegroundColor Cyan

# 1. Activar entorno virtual
$venvPath = "..\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "📦 Activando entorno virtual..." -ForegroundColor Yellow
    . $venvPath
} else {
    Write-Host "⚠️ No se encontró entorno virtual. Continuando con Python global." -ForegroundColor DarkYellow
}

# 2. Crear carpetas necesarias
New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null

# 3. Iniciar backend en una nueva ventana de PowerShell
Write-Host "🔧 Iniciando backend (puerto 8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001"

# 4. Iniciar frontend
$frontendDir = "frontend"
if (Test-Path $frontendDir) {
    Set-Location $frontendDir
    if (-not (Test-Path "node_modules")) {
        Write-Host "📦 Instalando dependencias del frontend..." -ForegroundColor Yellow
        npm install
    }
    Write-Host "🌐 Iniciando frontend..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev"
    Set-Location ..
} else {
    Write-Host "⚠️ Carpeta frontend no encontrada." -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "✅ Aplicación de Cobros en ejecución:" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presioná Enter para cerrar este script..." -ForegroundColor Gray
Read-Host