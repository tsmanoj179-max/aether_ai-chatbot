@echo off
title AetherAI CLI Terminal Workspace
echo ========================================================
echo         AetherAI CLI - Intelligent Terminal Mode
echo ========================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Initializing...
    python -m venv .venv
    call .\.venv\Scripts\pip.exe install -r backend\requirements.txt
)

.\.venv\Scripts\python.exe aether.py %*
