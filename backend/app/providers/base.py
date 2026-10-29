from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional
from backend.app.schemas.provider import ModelInfo

class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g. 'mock', 'gemini', 'groq', 'openai', 'ollama')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials/endpoints are configured."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify provider connection."""
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List supported models and their capability manifests."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate non-streaming response."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Yield streaming chunks: dict with 'type' ('token', 'tool_call', 'citation', 'done', 'error') and 'data'."""
        pass
