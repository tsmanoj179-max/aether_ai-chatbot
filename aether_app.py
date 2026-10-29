#!/usr/bin/env python
"""
AetherAI Universal Desktop & Web Application Supervisor.

Features:
- Completely hidden background execution (no black command prompt or terminal windows).
- Starts FastAPI backend and Vite frontend dev server with zero visible consoles.
- Launches AetherAI in native desktop app window mode (via Edge or Chrome --app).
- Automatic shutdown: When the application window or browser tab is closed,
  cleanly terminates backend, frontend, and all spawned processes.
"""

import os
import sys
import time
import signal
import atexit
import tempfile
import urllib.request
import urllib.error
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}/api/v1/health"
FRONTEND_URL = f"http://127.0.0.1:{FRONTEND_PORT}"

# Windows flag for invisible process creation
CREATE_NO_WINDOW = 0x08000000

# Global process handles
_backend_proc = None
_frontend_proc = None
_browser_proc = None
_is_shutting_down = False


def log(msg: str):
    """Log messages to a local log file for troubleshooting if needed."""
    log_file = os.path.join(tempfile.gettempdir(), "aetherai_launcher.log")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def get_pids_for_port(port: int):
    """Find process IDs listening on the given port on Windows."""
    pids = set()
    try:
        out = subprocess.check_output(["netstat", "-ano"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            line = line.strip()
            if f":{port}" in line and ("LISTENING" in line or "ESTABLISHED" in line):
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        pids.add(int(parts[-1]))
                    except ValueError:
                        pass
    except Exception as e:
        log(f"Error querying netstat for port {port}: {e}")
    return list(pids)


def kill_pids(pids):
    """Kill processes and their child trees forcefully."""
    for pid in pids:
        if pid <= 4:
            continue  # Protect system idle / system process
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                           capture_output=True, creationflags=CREATE_NO_WINDOW)
            log(f"Killed process tree for PID {pid}")
        except Exception as e:
            log(f"Failed to kill PID {pid}: {e}")


def cleanup():
    """Cleanly terminate all processes and free network ports."""
    global _is_shutting_down, _backend_proc, _frontend_proc, _browser_proc
    if _is_shutting_down:
        return
    _is_shutting_down = True
    log("Beginning application cleanup and shutdown sequence...")

    # Terminate spawned processes
    for proc, name in [(_frontend_proc, "Frontend"), (_backend_proc, "Backend")]:
        if proc and proc.poll() is None:
            try:
                log(f"Stopping {name} process (PID {proc.pid})...")
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               capture_output=True, creationflags=CREATE_NO_WINDOW)
            except Exception as e:
                log(f"Error terminating {name}: {e}")

    # Terminate any remaining processes on our dedicated ports
    kill_pids(get_pids_for_port(FRONTEND_PORT))
    kill_pids(get_pids_for_port(BACKEND_PORT))
    log("Cleanup complete. All AetherAI processes stopped.")


atexit.register(cleanup)


def check_url(url: str, timeout: float = 1.0) -> bool:
    """Check if an HTTP endpoint is responding."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AetherAI-Launcher/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 304)
    except Exception:
        return False


def get_python_exe():
    """Find the project virtual environment Python binary."""
    venv_py = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
    if os.path.exists(venv_py):
        return venv_py
    return sys.executable


def find_browser():
    """Find Microsoft Edge or Google Chrome to run in desktop App Mode."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def start_backend():
    """Start the FastAPI backend silently."""
    global _backend_proc
    log("Starting FastAPI backend...")
    python_exe = get_python_exe()
    env = os.environ.copy()
    env["AETHER_AUTO_SHUTDOWN"] = "1"
    env["PYTHONPATH"] = PROJECT_ROOT

    cmd = [
        python_exe,
        "-m", "uvicorn",
        "backend.app.main:app",
        "--host", "127.0.0.1",
        "--port", str(BACKEND_PORT)
    ]
    _backend_proc = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        env=env,
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    log(f"FastAPI backend started with PID {_backend_proc.pid}")


def start_frontend():
    """Start the Vite frontend dev server silently."""
    global _frontend_proc
    log("Starting Vite frontend dev server...")
    env = os.environ.copy()
    cmd = ["cmd.exe", "/c", "npm", "run", "dev"]
    _frontend_proc = subprocess.Popen(
        cmd,
        cwd=FRONTEND_DIR,
        env=env,
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    log(f"Frontend dev server started with PID {_frontend_proc.pid}")


def launch_app():
    """Main launcher and supervision loop."""
    global _browser_proc
    log("=== Launching AetherAI Application ===")

    # 1. Clean up any stale processes from earlier crashed runs
    if not check_url(BACKEND_URL):
        kill_pids(get_pids_for_port(BACKEND_PORT))
    if not check_url(FRONTEND_URL):
        kill_pids(get_pids_for_port(FRONTEND_PORT))

    # 2. Start Backend if not already responding
    if not check_url(BACKEND_URL):
        start_backend()

    # 3. Start Frontend if not already responding
    if not check_url(FRONTEND_URL):
        start_frontend()

    # 4. Wait for both services to become ready (up to 30 seconds)
    log("Waiting for services to become responsive...")
    start_time = time.time()
    backend_ready = False
    frontend_ready = False

    while time.time() - start_time < 30:
        if not backend_ready and check_url(BACKEND_URL):
            backend_ready = True
            log(f"Backend ready in {time.time() - start_time:.1f}s")
        if not frontend_ready and check_url(FRONTEND_URL):
            frontend_ready = True
            log(f"Frontend ready in {time.time() - start_time:.1f}s")

        if backend_ready and frontend_ready:
            break
        time.sleep(0.5)

    if not backend_ready or not frontend_ready:
        log("Warning: One or more services failed to respond within timeout.")

    # 5. Open Application Window
    browser_exe = find_browser()
    if browser_exe:
        log(f"Launching desktop window via: {browser_exe}")
        profile_dir = os.path.join(tempfile.gettempdir(), "aetherai_desktop_profile")
        os.makedirs(profile_dir, exist_ok=True)
        browser_cmd = [
            browser_exe,
            f"--app={FRONTEND_URL}",
            f"--user-data-dir={profile_dir}",
            "--name=AetherAI",
            "--window-size=1280,820",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        _browser_proc = subprocess.Popen(browser_cmd)
        log(f"Desktop application window opened (PID {_browser_proc.pid})")
    else:
        log("No Edge/Chrome detected; opening default web browser...")
        import webbrowser
        webbrowser.open(FRONTEND_URL)

    # 6. Supervision Loop: Watch for window closure or backend shutdown
    log("Supervisor loop active. Monitoring application state...")
    try:
        while True:
            # If native desktop window was opened and user closed it:
            if _browser_proc is not None:
                if _browser_proc.poll() is not None:
                    log("AetherAI desktop application window closed by user.")
                    break

            # Check if backend is still alive (if closed via browser beacon or exit button)
            if _backend_proc is not None and _backend_proc.poll() is not None:
                log("Backend process has exited.")
                break

            # Periodic check if backend service died or was shut down
            if not check_url(BACKEND_URL, timeout=1.5):
                # Double check with a brief sleep to avoid false positives
                time.sleep(1.0)
                if not check_url(BACKEND_URL, timeout=1.5):
                    log("Backend no longer responsive; initiating termination.")
                    break

            time.sleep(1.0)
    except KeyboardInterrupt:
        log("KeyboardInterrupt received in supervisor.")
    finally:
        cleanup()


if __name__ == "__main__":
    launch_app()
