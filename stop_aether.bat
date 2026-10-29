@echo off
cd /d "%~dp0"
echo ========================================================
echo       AetherAI - Clean Stop All Services
echo ========================================================

.\.venv\Scripts\python.exe -c "
import urllib.request, subprocess, sys
try:
    req = urllib.request.Request('http://127.0.0.1:8000/api/v1/system/shutdown', data=b'{\"immediate\": true}', headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req, timeout=1.0)
except Exception:
    pass

import aether_app
aether_app.kill_pids(aether_app.get_pids_for_port(8000))
aether_app.kill_pids(aether_app.get_pids_for_port(5173))
print('[OK] AetherAI backend, frontend, and all associated processes stopped.')
"

echo.
echo [DONE] All ports and services freed.
timeout /t 2 >nul
