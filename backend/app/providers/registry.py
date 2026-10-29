import asyncio
import logging
from typing import Dict, List, Optional, Tuple, AsyncGenerator, Any
from backend.app.config import settings
from backend.app.providers.base import BaseProvider
from backend.app.providers.mock_provider import MockProvider
from backend.app.providers.gemini_provider import GeminiProvider
from backend.app.providers.groq_provider import GroqProvider
from backend.app.providers.openai_provider import OpenAICompatibleProvider
from backend.app.providers.ollama_provider import OllamaProvider
from backend.app.providers.free_provider import FreeAIProvider
from backend.app.schemas.provider import ModelInfo, ProviderStatus

logger = logging.getLogger("aetherai.providers")

class ProviderRegistry:
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {
            "free_ai": FreeAIProvider(),
            "gemini": GeminiProvider(),
            "groq": GroqProvider(),
            "openai": OpenAICompatibleProvider(),
            "ollama": OllamaProvider(),
            "mock": MockProvider(),
        }

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        return self.providers.get(name)

    async def get_all_models(self) -> List[ModelInfo]:
        all_models: List[ModelInfo] = []
        for provider in self.providers.values():
            try:
                models = await provider.list_models()
                all_models.extend(models)
            except Exception as e:
                logger.warning(f"Error listing models for {provider.name}: {e}")
        return all_models

    async def get_providers_status(self) -> List[ProviderStatus]:
        status_list: List[ProviderStatus] = []
        for p in self.providers.values():
            is_cfg = p.is_configured()
            is_up = False
            error = None
            if is_cfg:
                try:
                    is_up = await p.health_check()
                except Exception as e:
                    error = str(e)
            try:
                models = await p.list_models()
            except Exception:
                models = []
            status_list.append(
                ProviderStatus(
                    name=p.name,
                    display_name=p.display_name,
                    is_configured=is_cfg,
                    is_available=is_up if is_cfg else False,
                    models=models,
                    error_message=error
                )
            )
        return status_list

    def resolve_provider_for_model(self, model_id: str) -> Tuple[Optional[BaseProvider], str]:
        """Resolves model string to appropriate provider and canonical model identifier."""
        if not model_id:
            model_id = settings.DEFAULT_MODEL

        if model_id.startswith("free-"):
            return self.providers["free_ai"], model_id

        if model_id.startswith("deepseek"):
            return self.providers["free_ai"], "free-deepseek-r1"

        if model_id.startswith("mistral") and not model_id.startswith("mixtral"):
            return self.providers["free_ai"], "free-mistral"

        if model_id.startswith("gemini"):
            return self.providers["gemini"], model_id

        if any(model_id.startswith(p) for p in ["llama", "mixtral", "gemma"]):
            return self.providers["groq"], model_id

        if model_id.startswith("gpt-") or model_id.startswith("o1-"):
            return self.providers["openai"], model_id

        if model_id.startswith("ollama"):
            return self.providers["ollama"], model_id

        if model_id.startswith("aether-mock") or model_id == "mock":
            return self.providers["mock"], model_id

        # Fallback to free_ai or configured default
        if "free_ai" in self.providers and self.providers["free_ai"].is_configured():
            return self.providers["free_ai"], model_id

        default_p = self.providers.get(settings.DEFAULT_PROVIDER)
        if default_p and default_p.is_configured():
            return default_p, model_id
        return self.providers["mock"], "aether-mock-omni"

    async def execute_stream_with_failover(
        self,
        messages: List[Dict[str, Any]],
        model_id: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes streaming generation with bounded failover.
        If primary provider encounters a rate limit or connection error, reports failover
        and attempts alternative configured provider or deterministic mock.
        """
        provider, target_model = self.resolve_provider_for_model(model_id)
        if not provider:
            provider = self.providers["mock"]
            target_model = "aether-mock-omni"

        # Check if provider is configured
        if not provider.is_configured() and provider.name != "mock":
            yield {
                "type": "status",
                "data": {
                    "status": f"Provider '{provider.display_name}' credentials not configured. Failing over to demonstration simulator...",
                    "provider": "mock"
                }
            }
            provider = self.providers["mock"]
            target_model = "aether-mock-omni"

        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                async for chunk in provider.generate_stream(
                    messages=messages,
                    model=target_model,
                    temperature=temperature,
                    system_prompt=system_prompt,
                    tools=tools
                ):
                    yield chunk
                return
            except Exception as e:
                logger.error(f"Provider {provider.name} attempt {attempt+1} failed: {e}")
                if attempt == 0 and provider.name != "mock":
                    yield {
                        "type": "status",
                        "data": {
                            "status": f"Temporary error with {provider.display_name}. Activating failover...",
                            "provider": "mock"
                        }
                    }
                    await asyncio.sleep(0.5)
                    provider = self.providers["mock"]
                    target_model = "aether-mock-omni"
                else:
                    yield {
                        "type": "error",
                        "data": {"error": f"Execution error: {str(e)}"}
                    }
                    return

provider_registry = ProviderRegistry()
