import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, JSON
from backend.app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AuditRecord(Base):
    __tablename__ = "audit_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # "tool_execution", "provider_call", "failover", "error"
    provider_used = Column(String(50), nullable=True)
    model_used = Column(String(100), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
