@echo off
cd /d "%~dp0"
title AetherAI Launcher

:: Check for virtual environment
if not exist ".venv\Scripts\pythonw.exe" (
    echo [ERROR] Virtual environment not found in .venv\Scripts\pythonw.exe
    echo Please run installation first.
    pause
    exit /b 1
)

:: Launch silently via VBScript without leaving any terminal window
if exist "AetherAI.vbs" (
    start "" wscript.exe //nologo "AetherAI.vbs"
    exit /b 0
)

:: Direct background fallback
start "" /B ".\.venv\Scripts\pythonw.exe" "aether_app.py"
exit /b 0
