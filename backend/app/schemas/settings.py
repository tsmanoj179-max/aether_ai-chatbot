from typing import Optional, Dict, Any
from pydantic import BaseModel

class UserSettings(BaseModel):
    theme: str = "dark"
    default_model: str = "aether-mock-omni"
    model_routing_enabled: bool = True
    memory_enabled: bool = True
    search_provider: str = "duckduckgo"
    temperature: float = 0.7
    system_prompt: Optional[str] = "You are AetherAI, an expert, thoughtful, and articulate AI workspace assistant."
    stream_responses: bool = True

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    database: str = "connected"
    active_provider: str
    configured_providers: Dict[str, bool]
    timestamp: str
