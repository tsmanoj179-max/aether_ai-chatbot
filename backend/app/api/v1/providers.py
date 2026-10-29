from typing import List
from fastapi import APIRouter
from backend.app.providers.registry import provider_registry
from backend.app.schemas.provider import ModelInfo, ProviderStatus

router = APIRouter(tags=["Providers & Models"])

@router.get("/providers", response_model=List[ProviderStatus])
async def list_providers():
    """Returns provider status list with availability and configured states."""
    return await provider_registry.get_providers_status()

@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """Returns capability registry of supported models."""
    return await provider_registry.get_all_models()
