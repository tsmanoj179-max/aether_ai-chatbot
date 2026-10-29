from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class MemoryCreate(BaseModel):
    content: str
    category: Optional[str] = "preference"

class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content: str
    category: str
    confidence: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    source_conversation_id: Optional[str] = None
