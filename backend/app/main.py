import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.api.v1 import api_v1_router
from backend.app.api.v1.system import auto_shutdown_watchdog

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aetherai")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database schema is ready
    logger.info("Initializing AetherAI persistence layer...")
    init_db()
    logger.info("AetherAI engine ready.")

    watchdog_task = None
    if os.environ.get("AETHER_AUTO_SHUTDOWN") == "1":
        watchdog_task = asyncio.create_task(auto_shutdown_watchdog())

    yield

    if watchdog_task and not watchdog_task.done():
        watchdog_task.cancel()

    # Shutdown
    logger.info("Shutting down AetherAI engine...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AetherAI Intelligent Workspace Backend API",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Safe Exception Handler (never leak raw stack traces)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.url.path}: {exc}", exc_info=settings.DEBUG)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing your request. Please try again or switch to demonstration simulator.",
            "detail": str(exc) if settings.DEBUG else None
        }
    )

# Mount API routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

# Mount static files for uploads and generated images
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "generated"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Root check
@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_PREFIX
    }
