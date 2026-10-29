@echo off
title AetherAI Frontend Client
echo ========================================================
echo  Starting AetherAI Frontend Client (Vite)
echo ========================================================
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [!] node_modules not found. Running npm install...
    call npm install
)

echo [*] Launching Vite dev server on http://127.0.0.1:5173 ...
call npm run dev
pause
