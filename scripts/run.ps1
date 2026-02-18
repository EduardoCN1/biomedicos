# run.ps1 - Script para arrancar la API
# Este script activa el entorno conda y ejecuta el servidor

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Arrancando API Biomedicos" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Verificar si .env existe
if (-not (Test-Path ".env")) {
    Write-Host "Advertencia: archivo .env no encontrado." -ForegroundColor Yellow
    Write-Host "Usando variables de entorno del sistema o valores por defecto." -ForegroundColor Yellow
    Write-Host "Para usar configuración personalizada, copia .env.example a .env" -ForegroundColor Yellow
} else {
    # Cargar variables desde .env (simple parser)
    Write-Host "Cargando configuración desde .env..." -ForegroundColor Yellow
    Get-Content .env | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value)
        }
    }
}

# Mostrar config
Write-Host "`nConfiguración:" -ForegroundColor Cyan
Write-Host "Neo4j URI: $($env:NEO4J_URI)" -ForegroundColor Gray
Write-Host "Neo4j User: $($env:NEO4J_USER)" -ForegroundColor Gray
Write-Host "API Host: $($env:HOST)" -ForegroundColor Gray
Write-Host "API Port: $($env:PORT)" -ForegroundColor Gray

# Activar entorno Conda
Write-Host "`nActivando entorno conda..." -ForegroundColor Yellow
# Inicializar conda para PowerShell si es necesario
& conda.bat "shell.powershell" "hook" | Out-String | Invoke-Expression
conda activate biomedicos

# Arrancar servidor
Write-Host "`nArrancando servidor en http://$($env:HOST):$($env:PORT)..." -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener.`n" -ForegroundColor Gray

python .\backend\run_waitress.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n✗ Error al arrancar el servidor" -ForegroundColor Red
    exit 1
}
