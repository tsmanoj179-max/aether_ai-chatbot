@echo off
title AetherAI Full-Stack Launcher
echo ========================================================
echo       AetherAI - Full Stack Development Launcher
echo ========================================================
cd /d "%~dp0"

echo [1/2] Starting Backend in a new window...
start "AetherAI Backend" cmd /c "run_backend.bat"

echo [2/2] Starting Frontend in a new window...
start "AetherAI Frontend" cmd /c "run_frontend.bat"

echo.
echo ========================================================
echo  [OK] AetherAI services are starting up!
echo       - Web Interface:   http://127.0.0.1:5173
echo       - Backend Health:  http://127.0.0.1:8000/api/v1/health
echo       - API Swagger:     http://127.0.0.1:8000/docs
echo       - CLI Mode:        run_cli.bat (or 'python aether.py')
echo ========================================================
echo You can close this launcher window at any time.
pause
