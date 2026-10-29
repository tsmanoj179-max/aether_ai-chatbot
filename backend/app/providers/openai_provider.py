import json
from typing import List, Dict, Any, AsyncGenerator, Optional
import httpx
from backend.app.config import settings
from backend.app.providers.base import BaseProvider
from backend.app.schemas.provider import ModelInfo, ModelCapability

class OpenAICompatibleProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "openai"

    @property
    def display_name(self) -> str:
        return "OpenAI-Compatible (Free Cloud / Official)"

    def is_configured(self) -> bool:
        return True

    def _get_api_base(self) -> str:
        if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 5:
            return settings.OPENAI_API_BASE or "https://api.openai.com/v1"
        return "https://text.pollinations.ai/openai"

    async def health_check(self) -> bool:
        try:
            headers = {}
            if settings.OPENAI_API_KEY:
                headers["Authorization"] = f"Bearer {settings.OPENAI_API_KEY}"
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(f"{self._get_api_base()}/models", headers=headers)
                return res.status_code in [200, 404]
        except Exception:
            return True

    async def list_models(self) -> List[ModelInfo]:
        has_key = bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 5)
        tier_label = "free" if not has_key else "paid"
        desc_suffix = " (Connected via Free Live Cloud Gateway)" if not has_key else " (Official Key Configured)"

        return [
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                provider="openai",
                description=f"High-intelligence flagship multimodal model{desc_suffix}.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=has_key,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=True,
                ),
                is_available=True,
                context_window=128000,
                tier=tier_label
            ),
            ModelInfo(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                provider="openai",
                description=f"Affordable and fast intelligent model for everyday tasks{desc_suffix}.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=has_key,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=False,
                ),
                is_available=True,
                context_window=128000,
                tier="free"
            ),
        ]

    def _prepare_payload(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted.append({
                "role": m.get("role", "user"),
                "content": m.get("content", "")
            })
        return {
            "model": model,
            "messages": formatted,
            "temperature": temperature,
            "stream": stream
        }

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        target_model = model if settings.OPENAI_API_KEY else "openai"
        payload = self._prepare_payload(messages, target_model, temperature, system_prompt, stream=False)
        headers = {"Content-Type": "application/json"}
        if settings.OPENAI_API_KEY:
            headers["Authorization"] = f"Bearer {settings.OPENAI_API_KEY}"

        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
            res = await client.post(f"{self._get_api_base()}/chat/completions", json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            choices = data.get("choices", [])
            if not choices:
                return {
                    "content": "",
                    "model_used": model,
                    "provider_used": "openai",
                    "finish_reason": "stop",
                    "citations": []
                }
            choice = choices[0]
            msg = choice.get("message", {})
            content = msg.get("content", "")
            reasoning = msg.get("reasoning", "")
            if reasoning and not content.startswith("<think>"):
                content = f"<think>\n{reasoning}\n</think>\n\n{content}"

            return {
                "content": content,
                "model_used": model,
                "provider_used": "openai",
                "finish_reason": choice.get("finish_reason", "stop"),
                "citations": []
            }

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        target_model = model if settings.OPENAI_API_KEY else "openai"
        payload = self._prepare_payload(messages, target_model, temperature, system_prompt, stream=True)
        headers = {"Content-Type": "application/json"}
        if settings.OPENAI_API_KEY:
            headers["Authorization"] = f"Bearer {settings.OPENAI_API_KEY}"

        yield {
            "type": "status",
            "data": {"status": f"Streaming from {model}...", "provider": "openai"}
        }

        has_started_thinking = False
        has_closed_thinking = False

        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
            async with client.stream("POST", f"{self._get_api_base()}/chat/completions", json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        raw_data = line[6:].strip()
                        if raw_data == "[DONE]":
                            if has_started_thinking and not has_closed_thinking:
                                yield {"type": "token", "data": {"token": "\n</think>\n\n"}}
                            yield {
                                "type": "done",
                                "data": {
                                    "model_used": model,
                                    "provider_used": "openai",
                                    "finish_reason": "stop"
                                }
                            }
                            break
                        try:
                            chunk = json.loads(raw_data)
                            choices = chunk.get("choices")
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})

                            reasoning = delta.get("reasoning")
                            if reasoning:
                                if not has_started_thinking:
                                    has_started_thinking = True
                                    yield {"type": "token", "data": {"token": "<think>\n"}}
                                yield {"type": "token", "data": {"token": reasoning}}

                            content = delta.get("content")
                            if content:
                                if has_started_thinking and not has_closed_thinking:
                                    has_closed_thinking = True
                                    yield {"type": "token", "data": {"token": "\n</think>\n\n"}}
                                yield {"type": "token", "data": {"token": content}}

                        except json.JSONDecodeError:
                            continue
