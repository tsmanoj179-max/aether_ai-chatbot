import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "AetherAI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Network and server binding (security: default to localhost only)
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Persistence
    DATABASE_URL: str = "sqlite:///./aetherai.db"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx",
        ".png", ".jpg", ".jpeg", ".webp"
    ]
    
    # AI Providers Configuration
    DEFAULT_PROVIDER: str = "gemini"
    DEFAULT_MODEL: str = "gemini-2.5-flash"
    
    GEMINI_API_KEY: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    GROQ_API_KEY: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    OPENAI_API_BASE: Optional[str] = Field(default="https://api.openai.com/v1", alias="OPENAI_API_BASE")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    
    # Search Providers
    TAVILY_API_KEY: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    BRAVE_API_KEY: Optional[str] = Field(default=None, alias="BRAVE_API_KEY")
    
    # RAG parameters
    RAG_CHUNK_SIZE: int = 600
    RAG_CHUNK_OVERLAP: int = 100
    RAG_TOP_K: int = 4
    RAG_SIMILARITY_THRESHOLD: float = 0.25
    
    # Rate Limiting & Resource Protection
    MAX_CONCURRENT_RESEARCH_TASKS: int = 2
    REQUEST_TIMEOUT_SECONDS: int = 60

settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
