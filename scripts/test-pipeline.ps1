# Test script for TNM Pipeline Architecture
# Valida que TNM llega al recommender service y regresa resultado

$API_URL = "http://localhost:5000"
$TNM_DATA = @{
    job_id = ""
    tnm = @{
        t_label = "T1"
        n_label = "N0"
        m_label = "M0"
    }
} | ConvertTo-Json

Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🧪 PRUEBA DE ARQUITECTURA TNM → RECOMENDADOR → VALIDADOR" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar salud del pipeline
Write-Host "[1/5] Verificando salud del pipeline..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$API_URL/pipeline/health" -Method GET
    Write-Host "✓ Pipeline health:" -ForegroundColor Green
    $health | ConvertTo-Json | Write-Host
} catch {
    Write-Host "✗ Error verificando health:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""

# 2. Enviar TNM al pipeline
Write-Host "[2/5] Enviando TNM (T1, N0, M0) al pipeline..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/pipeline/submit" -Method POST `
        -ContentType "application/json" `
        -Body $TNM_DATA
    $JOB_ID = $response.job_id
    Write-Host "✓ TNM enviado correctamente" -ForegroundColor Green
    Write-Host "  Job ID: $JOB_ID" -ForegroundColor Cyan
    Write-Host "  Status: $($response.status)" -ForegroundColor Cyan
} catch {
    Write-Host "✗ Error enviando TNM:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""

# 3. Mostrar logs en tiempo real (opcional)
Write-Host "[3/5] Mostrando logs de microservicios (5 segundos)..." -ForegroundColor Yellow
Write-Host "═════════════════════════════════════════════════════" -ForegroundColor Gray
$logProcess = Start-Process docker -ArgumentList "compose logs --tail 20 -f" -NoNewWindow -PassThru
Start-Sleep -Seconds 5
Stop-Process -Id $logProcess.Id -Force -ErrorAction SilentlyContinue
Write-Host "═════════════════════════════════════════════════════" -ForegroundColor Gray

Write-Host ""

# 4. Verificar estado del job en el debug endpoint
Write-Host "[4/5] Verificando estado interno del job..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    $debug = Invoke-RestMethod -Uri "$API_URL/pipeline/debug" -Method GET
    Write-Host "✓ Debug info:" -ForegroundColor Green
    Write-Host "  Total jobs: $($debug.total_jobs)" -ForegroundColor Cyan
    if ($debug.jobs.$JOB_ID) {
        Write-Host "  Job ${JOB_ID}:" -ForegroundColor Cyan
        $debug.jobs.$JOB_ID | ConvertTo-Json | ForEach-Object { Write-Host "    $_" }
    }
} catch {
    Write-Host "⚠ No se pudo acceder a debug:" -ForegroundColor Yellow
}

Write-Host ""

# 5. Polling para obtener resultado
Write-Host "[5/5] Esperando resultado del pipeline (máx 30 segundos)..." -ForegroundColor Yellow
$attempts = 0
$max_attempts = 15
$found_result = $false

while ($attempts -lt $max_attempts) {
    try {
        $result = Invoke-RestMethod -Uri "$API_URL/pipeline/result/$JOB_ID" -Method GET
        
        Write-Host "  Intento $($attempts + 1)/$max_attempts - Status: $($result.status)" -ForegroundColor Cyan
        
        if ($result.status -eq "completed" -and $result.result) {
            $found_result = $true
            Write-Host ""
            Write-Host "✓ RESULTADO RECIBIDO - TNM PROCESADO CORRECTAMENTE:" -ForegroundColor Green
            Write-Host "═════════════════════════════════════════════════════" -ForegroundColor Green
            $result.result | ConvertTo-Json | Write-Host
            Write-Host "═════════════════════════════════════════════════════" -ForegroundColor Green
            break
        } elseif ($result.status -eq "failed") {
            Write-Host "✗ Job falló:" -ForegroundColor Red
            $result | ConvertTo-Json | Write-Host
            break
        }
    } catch {
        Write-Host "  Intento $($attempts + 1)/$max_attempts - Esperando..." -ForegroundColor Gray
    }
    
    $attempts++
    Start-Sleep -Seconds 2
}

Write-Host ""

if ($found_result) {
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "✓ PRUEBA EXITOSA - ARQUITECTURA VALIDADA" -ForegroundColor Green
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "El flujo TNM → Recommender → Validator → Result funcionó correctamente" -ForegroundColor Green
} else {
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host "⚠ TIMEOUT - No se recibió resultado en 30 segundos" -ForegroundColor Yellow
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Verifica los logs con: docker compose logs" -ForegroundColor Yellow
}
