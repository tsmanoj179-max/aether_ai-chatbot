from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.providers.registry import provider_registry
from backend.app.schemas.settings import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
async def check_health(db: Session = Depends(get_db)):
    # Verify DB connectivity
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check providers status
    providers_status = {}
    for name, prov in provider_registry.providers.items():
        providers_status[name] = prov.is_configured()

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=settings.VERSION,
        database=db_status,
        active_provider=settings.DEFAULT_PROVIDER,
        configured_providers=providers_status,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
