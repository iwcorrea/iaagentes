# ============================================================
# APLICACIÓN DE COBROS – Arranque rápido (v4 - Corrección de Colores)
# ============================================================
Clear-Host
Write-Host "🚀 Iniciando Aplicación de Cobros..." -ForegroundColor Cyan

# 1. Activar entorno virtual del ecosistema de manera robusta
$venvPath = Join-Path (Get-Location).Path "..\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "📦 Activando entorno virtual..." -ForegroundColor Yellow
    . $venvPath
} else {
    Write-Host "⚠️ No se encontró el entorno virtual. Continuando con Python global..." -ForegroundColor DarkYellow
}

# Crear carpetas estructurales necesarias
$null = New-Item -ItemType Directory -Force -Path ".\logs"
$null = New-Item -ItemType Directory -Force -Path ".\backend"
$null = New-Item -ItemType Directory -Force -Path ".\frontend"

# 2. Backend
Write-Host "🔧 Iniciando backend (puerto 8001)..." -ForegroundColor Yellow
$backendJob = Start-Job -Name "CobrosBackend" -ScriptBlock {
    param($pwd)
    Set-Location $pwd
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
} -ArgumentList (Get-Location).Path

# 3. Frontend - Forzar verificación real de Vite
$frontendDir = Join-Path (Get-Location) "frontend"
if (Test-Path $frontendDir) {
    Set-Location $frontendDir

    if (-not (Test-Path "package.json")) {
        Write-Host "❌ No se encontró package.json en frontend/. Asegurate de que el proyecto existe." -ForegroundColor Red
        Set-Location ..
    } else {
        # MEJORA: Comprobar si el EJECUTABLE de vite existe, no solo la carpeta node_modules
        $viteBinPath = ".\node_modules\.bin\vite"
        if (-not (Test-Path $viteBinPath) -and -not (Test-Path "$viteBinPath.cmd")) {
            Write-Host "📦 Vite no está instalado o está corrupto. Limpiando e instalando dependencias..." -ForegroundColor Yellow
            
            # Borrar node_modules corrupto si existe para empezar limpio
            if (Test-Path "node_modules") {
                Remove-Item -Recurse -Force "node_modules" -ErrorAction SilentlyContinue
            }

            # Instalación limpia y visible
            npm install
            
            # Segunda verificación después de instalar
            if (-not (Test-Path $viteBinPath) -and -not (Test-Path "$viteBinPath.cmd")) {
                Write-Host "❌ Error crítico: 'npm install' falló y no pudo generar Vite." -ForegroundColor Red
                Write-Host "💡 Sugerencia: Entra a la carpeta 'frontend' manualmente y ejecuta 'npm install'." -ForegroundColor Yellow
                Set-Location ..
                Exit
            }
            Write-Host "✅ Dependencias instaladas correctamente." -ForegroundColor Green
        }

        Write-Host "🌐 Iniciando frontend con Vite..." -ForegroundColor Yellow
        Start-Process cmd -ArgumentList "/c npm run dev" -NoNewWindow
        Set-Location ..
    }
} else {
    Write-Host "⚠️ No se encontró la carpeta frontend." -ForegroundColor DarkYellow
}

# Mensaje de éxito consolidado (Cambiado LightGreen por Green)
Write-Host ""
Write-Host "✅ Ecosistema de Cobros Desplegado:" -ForegroundColor Green
Write-Host "   Backend API:  http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "   Frontend Web: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presioná ENTER para detener de forma segura todos los servicios..." -ForegroundColor Green
Write-Host ""

# Cierre limpio de procesos al presionar Enter
Read-Host
Write-Host "🛑 Deteniendo servicios..." -ForegroundColor Yellow

if ($backendJob) {
    Stop-Job -Name "CobrosBackend"
    Remove-Job -Name "CobrosBackend"
}

# Cerramos cualquier instancia de Node/Vite levantada por el script
Stop-Process -Name "node" -ErrorAction SilentlyContinue

Write-Host "✅ Aplicación detenida con éxito." -ForegroundColor Gray
