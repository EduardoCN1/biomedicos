# setup.ps1 - Script de configuración inicial para Windows
# Este script instala Miniforge/Conda y crea el entorno biomedicos

Write-Host "================================" -ForegroundColor Green
Write-Host "Setup del Proyecto Biomedicos" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Verificar si Conda está instalado
Write-Host "Verificando Conda..." -ForegroundColor Yellow
$condaExists = $null
try {
    $condaExists = conda --version 2>$null
} catch {}

if ($null -eq $condaExists) {
    Write-Host "Conda no encontrado. Por favor instala Miniforge:" -ForegroundColor Red
    Write-Host "https://github.com/conda-forge/miniforge" -ForegroundColor Cyan
    exit 1
}

Write-Host "✓ Conda detectado: $condaExists" -ForegroundColor Green

# Crear entorno
Write-Host "`nCreando entorno 'biomedicos'..." -ForegroundColor Yellow
conda create -n biomedicos python=3.11 -y
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al crear entorno conda" -ForegroundColor Red
    exit 1
}

# Activar entorno y instalar dependencias
Write-Host "`nActivando entorno y instalando dependencias..." -ForegroundColor Yellow
conda activate biomedicos
conda install -c conda-forge numpy pandas -y
python -m pip install --upgrade pip setuptools wheel
python -m pip install --prefer-binary -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Setup completado exitosamente!" -ForegroundColor Green
    Write-Host "`nPasos siguientes:" -ForegroundColor Cyan
    Write-Host "1. Copia .env.example a .env y configura las credenciales Neo4j" -ForegroundColor Cyan
    Write-Host "2. Ejecuta: .\scripts\run.ps1" -ForegroundColor Cyan
} else {
    Write-Host "`n✗ Error durante la instalación" -ForegroundColor Red
    exit 1
}
