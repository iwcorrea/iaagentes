# ============================================================
# APLICACIÓN DE COBROS – Arranque rápido (v2)
# ============================================================
Write-Host "🚀 Iniciando Aplicación de Cobros..." -ForegroundColor Cyan

# 1. Activar entorno virtual del ecosistema (opcional)
$venvPath = "..\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "📦 Activando entorno virtual..." -ForegroundColor Yellow
    . $venvPath
} else {
    Write-Host "⚠️ No se encontró el entorno virtual. Continuando sin él." -ForegroundColor DarkYellow
}

# Crear carpetas necesarias
New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null
New-Item -ItemType Directory -Force -Path ".\backend" | Out-Null
New-Item -ItemType Directory -Force -Path ".\frontend" | Out-Null

# 2. Backend
Write-Host "🔧 Iniciando backend (puerto 8001)..." -ForegroundColor Yellow
$backendJob = Start-Job -Name "CobrosBackend" -ScriptBlock {
    param($pwd)
    Set-Location $pwd
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
} -ArgumentList (Get-Location).Path

# 3. Frontend
$frontendDir = Join-Path (Get-Location) "frontend"
if (Test-Path $frontendDir) {
    Set-Location $frontendDir

    # Verificar que package.json existe
    if (-not (Test-Path "package.json")) {
        Write-Host "❌ No se encontró package.json en frontend/. Asegurate de que el frontend fue generado correctamente." -ForegroundColor Red
        Set-Location ..
    } else {
        # Instalar dependencias si no existen
        if (-not (Test-Path "node_modules")) {
            Write-Host "📦 Instalando dependencias del frontend..." -ForegroundColor Yellow
            npm install 2>&1 | Out-File "..\logs\frontend_cobros.log"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "❌ Error al instalar dependencias. Revisá ..\\logs\\frontend_cobros.log" -ForegroundColor Red
                Set-Location ..
            } else {
                Write-Host "✅ Dependencias instaladas." -ForegroundColor Green
            }
        }

        Write-Host "🌐 Iniciando frontend..." -ForegroundColor Yellow
        Start-Process -NoNewWindow npm -ArgumentList "run", "dev"
        Set-Location ..
    }
} else {
    Write-Host "⚠️ No se encontró la carpeta frontend." -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "✅ Aplicación de Cobros en ejecución:" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presioná Ctrl+C para detener el backend. Luego ejecutá:" -ForegroundColor Gray
Write-Host "  Get-Job | Stop-Job" -ForegroundColor Gray
Write-Host ""

# Mantener la ventana abierta hasta que se presione una tecla
Read-Host "Presioná Enter para detener todo..."
if ($backendJob) {
    Stop-Job -Name "CobrosBackend"
    Remove-Job -Name "CobrosBackend"
}
Write-Host "🛑 Aplicación detenida." -ForegroundColor Gray