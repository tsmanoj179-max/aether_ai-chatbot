from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

class MessageBase(BaseModel):
    role: str
    content: str
    attachments: Optional[List[Dict[str, Any]]] = None

class MessageCreate(MessageBase):
    pass

class MessageFeedbackUpdate(BaseModel):
    feedback: Optional[str] = Field(None, pattern="^(like|dislike|none)$")

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    feedback: Optional[str] = None

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    model_id: Optional[str] = "aether-mock-omni"
    system_prompt: Optional[str] = None
    folder: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    pinned: Optional[bool] = None
    folder: Optional[str] = None
    model_id: Optional[str] = None
    system_prompt: Optional[str] = None

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    pinned: bool
    folder: Optional[str] = None
    model_id: str
    system_prompt: Optional[str] = None
    message_count: int = 0
    last_message: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    model_id: Optional[str] = None
    system_prompt: Optional[str] = None
    web_search: bool = False
    deep_research: bool = False
    collection_name: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    temperature: Optional[float] = 0.7
    stream: bool = True

class RegenerateRequest(BaseModel):
    message_id: str
    model_id: Optional[str] = None
