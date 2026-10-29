import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system", "tool"
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=utc_now, nullable=False)
    
    # Metadata for provenance & transparency
    model_used = Column(String(100), nullable=True)
    provider_used = Column(String(50), nullable=True)
    finish_reason = Column(String(50), nullable=True)
    
    # Structured fields: tool calls executed, citation references, attachments
    tool_calls = Column(JSON, nullable=True)
    citations = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)
    
    # User feedback: "like", "dislike", or null
    feedback = Column(String(20), nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
