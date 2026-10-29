# ==============================================================================
# AetherAI Unified Development Runner (Windows PowerShell)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       AetherAI - Full Stack Development Environment       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$RootPath = $PSScriptRoot

# Start Backend Process
Write-Host "[1/2] Launching Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$BackendProcess = Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$RootPath\run_backend.ps1" -PassThru

# Start Frontend Process
Write-Host "[2/2] Launching Frontend on http://127.0.0.1:5173..." -ForegroundColor Green
$FrontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$RootPath\run_frontend.ps1" -PassThru

Write-Host ""
Write-Host "[✓] AetherAI is starting up!" -ForegroundColor Cyan
Write-Host "    - Application UI:  http://127.0.0.1:5173" -ForegroundColor White
Write-Host "    - Backend Health:  http://127.0.0.1:8000/api/v1/health" -ForegroundColor White
Write-Host "    - OpenAPI Docs:    http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Close the spawned PowerShell windows or press Ctrl+C to terminate." -ForegroundColor Gray
