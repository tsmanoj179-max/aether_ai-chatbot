# ==============================================================================
# AetherAI Backend Startup Script (Windows PowerShell)
# ==============================================================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Starting AetherAI Backend Server..." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$VENV_PYTHON = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-Not (Test-Path $VENV_PYTHON)) {
    Write-Host "[!] Virtual environment not found. Creating .venv..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "[*] Installing dependencies..." -ForegroundColor Yellow
    & ".\.venv\Scripts\pip.exe" install -r backend\requirements.txt
}

Write-Host "[*] Launching FastAPI uvicorn server on http://127.0.0.1:8000 ..." -ForegroundColor Green
Write-Host "[*] Interactive API docs available at http://127.0.0.1:8000/docs" -ForegroundColor Gray

& $VENV_PYTHON -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
