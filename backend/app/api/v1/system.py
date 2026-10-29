import os
import time
import asyncio
import logging
import threading
import subprocess
from typing import Optional
from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger("aetherai.system")

router = APIRouter(prefix="/system", tags=["System"])

# In-memory tracking
_startup_time = time.time()
_last_heartbeat = time.time()
_pending_shutdown_timer: Optional[threading.Timer] = None
_shutdown_lock = threading.Lock()
_has_received_heartbeat = False


class HeartbeatPayload(BaseModel):
    client_id: Optional[str] = None
    action: Optional[str] = "ping"


class ShutdownPayload(BaseModel):
    immediate: Optional[bool] = False
    reason: Optional[str] = "user_exit"


def update_heartbeat():
    """Update the heartbeat timestamp and cancel any pending graceful shutdown."""
    global _last_heartbeat, _has_received_heartbeat, _pending_shutdown_timer
    _last_heartbeat = time.time()
    _has_received_heartbeat = True
    with _shutdown_lock:
        if _pending_shutdown_timer is not None:
            logger.info("New heartbeat received: cancelling pending graceful shutdown.")
            _pending_shutdown_timer.cancel()
            _pending_shutdown_timer = None


def execute_system_exit(immediate: bool = False):
    """Cleanly terminates backend and any associated processes."""
    logger.info("Executing system exit: freeing resources and shutting down...")
    
    def _do_exit():
        if not immediate:
            time.sleep(0.5)
        # Flush standard streams
        import sys
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass
        os._exit(0)

    t = threading.Thread(target=_do_exit, daemon=True)
    t.start()


@router.post("/heartbeat")
async def receive_heartbeat(payload: Optional[HeartbeatPayload] = None):
    """Endpoint called periodically by active frontend tabs to signal user presence."""
    update_heartbeat()
    return {
        "status": "alive",
        "timestamp": _last_heartbeat,
        "uptime_seconds": round(time.time() - _startup_time, 1)
    }


@router.get("/heartbeat")
async def check_heartbeat():
    """GET heartbeat support for simple ping checks."""
    update_heartbeat()
    return {
        "status": "alive",
        "timestamp": _last_heartbeat,
        "uptime_seconds": round(time.time() - _startup_time, 1)
    }


@router.post("/shutdown")
async def trigger_shutdown(request: Request):
    """
    Called when a user closes the application, exits via UI, or tab unloads (via navigator.sendBeacon).
    Supports JSON, form data, or empty body.
    """
    global _pending_shutdown_timer
    immediate = False
    try:
        body = await request.body()
        if body:
            import json
            data = json.loads(body.decode("utf-8"))
            if isinstance(data, dict) and data.get("immediate"):
                immediate = True
    except Exception:
        pass

    with _shutdown_lock:
        if immediate:
            logger.info("Immediate shutdown requested by user.")
            if _pending_shutdown_timer is not None:
                _pending_shutdown_timer.cancel()
                _pending_shutdown_timer = None
            execute_system_exit(immediate=True)
            return {"status": "shutting_down", "immediate": True}
        else:
            # Graceful shutdown with 3.5s grace period:
            # If the user is only reloading the page (F5), the new page will send a heartbeat
            # within 1-2 seconds and cancel this timer.
            # If the user closed the window/tab, no heartbeat will follow and shutdown executes.
            if _pending_shutdown_timer is not None:
                _pending_shutdown_timer.cancel()
            
            logger.info("Client unload detected; scheduled graceful shutdown in 3.5s unless heartbeat resumes...")
            _pending_shutdown_timer = threading.Timer(3.5, execute_system_exit, args=[False])
            _pending_shutdown_timer.daemon = True
            _pending_shutdown_timer.start()

            return {
                "status": "pending_shutdown",
                "grace_period_seconds": 3.5,
                "message": "Shutdown will execute if no active frontend heartbeat resumes."
            }


async def auto_shutdown_watchdog():
    """
    Background watchdog loop active when AETHER_AUTO_SHUTDOWN=1.
    If no frontend sends a heartbeat for more than 10 seconds (after initial 30s grace period),
    automatically shuts down backend to avoid orphaned processes.
    """
    if os.environ.get("AETHER_AUTO_SHUTDOWN") != "1":
        return

    logger.info("AetherAI Auto-Shutdown Watchdog is ACTIVE. Will auto-terminate if UI disconnects.")
    
    # Initial startup grace period (wait for frontend dev server / browser to start)
    await asyncio.sleep(25)

    while True:
        await asyncio.sleep(2)
        idle_time = time.time() - _last_heartbeat
        # If client has connected before and has been silent for > 10s, OR
        # if client never connected even after 60s total
        total_uptime = time.time() - _startup_time
        if (_has_received_heartbeat and idle_time > 10.0) or (not _has_received_heartbeat and total_uptime > 60.0):
            logger.info(f"Auto-shutdown triggered: Idle time is {idle_time:.1f}s. Exiting AetherAI backend.")
            execute_system_exit(immediate=True)
            break
