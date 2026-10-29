@echo off
title AetherAI Backend Server
echo ========================================================
echo  Starting AetherAI Backend Server (FastAPI / Uvicorn)
echo ========================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Creating .venv...
    python -m venv .venv
    echo [*] Installing dependencies...
    call .\.venv\Scripts\pip.exe install -r backend\requirements.txt
)

echo [*] Launching FastAPI on http://127.0.0.1:8000 ...
echo [*] Interactive docs available at http://127.0.0.1:8000/docs
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
