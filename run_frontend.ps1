# ==============================================================================
# AetherAI Frontend Startup Script (Windows PowerShell)
# ==============================================================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Starting AetherAI Frontend (Vite)..." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

Set-Location (Join-Path $PSScriptRoot "frontend")

if (-Not (Test-Path "node_modules")) {
    Write-Host "[!] node_modules not found. Running npm install..." -ForegroundColor Yellow
    cmd /c "npm install"
}

Write-Host "[*] Launching Vite development server at http://127.0.0.1:5173 ..." -ForegroundColor Green
cmd /c "npm run dev"
