from typing import List, Optional
from pydantic import BaseModel

class ModelCapability(BaseModel):
    streaming: bool = True
    vision: bool = False
    tool_calling: bool = True
    structured_output: bool = True
    web_search: bool = True
    deep_research: bool = True

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: str
    capabilities: ModelCapability
    is_available: bool = True
    context_window: int = 8192
    tier: str = "free"  # free, paid, local, mock

class ProviderStatus(BaseModel):
    name: str
    display_name: str
    is_configured: bool
    is_available: bool
    models: List[ModelInfo]
    error_message: Optional[str] = None
