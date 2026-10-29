# AetherAI CLI Terminal Workspace Launcher
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "[!] Virtual environment not found. Initializing..." -ForegroundColor Yellow
    python -m venv .venv
    .\.venv\Scripts\pip.exe install -r backend\requirements.txt
}

.\.venv\Scripts\python.exe aether.py @args
