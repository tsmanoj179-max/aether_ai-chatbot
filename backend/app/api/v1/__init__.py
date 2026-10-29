from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.providers import router as providers_router
from backend.app.api.v1.conversations import router as conversations_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.memories import router as memories_router
from backend.app.api.v1.tools import router as tools_router
from backend.app.api.v1.settings import router as settings_router
from backend.app.api.v1.research import router as research_router
from backend.app.api.v1.images import router as images_router
from backend.app.api.v1.system import router as system_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(providers_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(memories_router)
api_v1_router.include_router(tools_router)
api_v1_router.include_router(settings_router)
api_v1_router.include_router(research_router)
api_v1_router.include_router(images_router)
api_v1_router.include_router(system_router)
