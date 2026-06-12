# ============================================================
# APLICACIÓN DE COBROS – Arranque rápido (v3 - Optimizado)
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

# 2. Backend - Validación previa de dependencias básicas
Write-Host "🔧 Iniciando backend (puerto 8001)..." -ForegroundColor Yellow
$backendJob = Start-Job -Name "CobrosBackend" -ScriptBlock {
    param($pwd)
    Set-Location $pwd
    # Ejecución como módulo de Python para evitar fallos de PATH en Windows
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
} -ArgumentList (Get-Location).Path

# 3. Frontend - Optimizado y Visible
$frontendDir = Join-Path (Get-Location) "frontend"
if (Test-Path $frontendDir) {
    Set-Location $frontendDir

    if (-not (Test-Path "package.json")) {
        Write-Host "❌ No se encontró package.json en frontend/. Asegurate de que el proyecto existe." -ForegroundColor Red
        Set-Location ..
    } else {
        # MEJORA CLAVE: Si no hay node_modules, mostramos la instalación en tiempo real para ver errores
        if (-not (Test-Path "node_modules")) {
            Write-Host "📦 'node_modules' no detectado. Instalando dependencias en primer plano..." -ForegroundColor Yellow
            
            # Limpiamos caché por si acaso y forzamos instalación visible
            npm cache clean --force | Out-Null
            npm install
            
            # Verificación real del ejecutable crítico
            $vitePath = ".\node_modules\.bin\vite"
            if (-not (Test-Path $vitePath) -and -not (Test-Path "$vitePath.cmd")) {
                Write-Host "❌ Error crítico: Vite no se instaló correctamente debido a conflictos de paquetes." -ForegroundColor Red
                Write-Host "💡 Sugerencia: Ejecuta 'npm install --legacy-peer-deps' manualmente en la carpeta frontend." -ForegroundColor DarkYellow
                Set-Location ..
                Exit
            }
            Write-Host "✅ Dependencias instaladas correctamente." -ForegroundColor Green
        }

        Write-Host "🌐 Iniciando frontend con Vite..." -ForegroundColor Yellow
        # Usamos Start-Process para abrir el servidor en una ventana secundaria y no bloquear la terminal principal
        Start-Process cmd -ArgumentList "/c npm run dev" -NoNewWindow
        Set-Location ..
    }
} else {
    Write-Host "⚠️ No se encontró la carpeta frontend." -ForegroundColor DarkYellow
}

# Mensaje de éxito consolidado
Write-Host ""
Write-Host "✅ Ecosistema de Cobros Desplegado:" -ForegroundColor Green
Write-Host "   Backend API:  http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "   Frontend Web: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presioná ENTER para detener de forma segura todos los servicios..." -ForegroundColor LightGreen
Write-Host ""

# Cierre limpio de procesos al presionar Enter
Read-Host
Write-Host "🛑 Deteniendo servicios..." -ForegroundColor Yellow

if ($backendJob) {
    Stop-Job -Name "CobrosBackend"
    Remove-Job -Name "CobrosBackend"
}

# Cerramos cualquier instancia huérfana de Node/Vite levantada por el script
Stop-Process -Name "node" -ErrorAction SilentlyContinue

Write-Host "✅ Aplicación detenida con éxito." -ForegroundColor Gray
