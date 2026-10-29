from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from backend.app.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
