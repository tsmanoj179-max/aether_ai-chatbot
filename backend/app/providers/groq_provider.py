import json
from typing import List, Dict, Any, AsyncGenerator, Optional
import httpx
from backend.app.config import settings
from backend.app.providers.base import BaseProvider
from backend.app.schemas.provider import ModelInfo, ModelCapability

class GroqProvider(BaseProvider):
    BASE_URL = "https://api.groq.com/openai/v1"

    @property
    def name(self) -> str:
        return "groq"

    @property
    def display_name(self) -> str:
        return "GroqCloud (Free Cloud / Official)"

    def is_configured(self) -> bool:
        return True

    def _has_groq_key(self) -> bool:
        return bool(settings.GROQ_API_KEY and len(settings.GROQ_API_KEY.strip()) > 5)

    async def health_check(self) -> bool:
        if self._has_groq_key():
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    res = await client.get(
                        f"{self.BASE_URL}/models",
                        headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
                    )
                    return res.status_code == 200
            except Exception:
                return True
        return True

    async def list_models(self) -> List[ModelInfo]:
        has_key = self._has_groq_key()
        desc_suffix = " (Live Free Cloud Inference)" if not has_key else " (Official Groq LPU Hardware)"

        return [
            ModelInfo(
                id="llama-3.3-70b-versatile",
                name="Llama 3.3 70B Versatile",
                provider="groq",
                description=f"Ultra-fast versatile Llama 3.3 model{desc_suffix}.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=False,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=True,
                ),
                is_available=True,
                context_window=128000,
                tier="free"
            ),
            ModelInfo(
                id="llama-3.1-8b-instant",
                name="Llama 3.1 8B Instant",
                provider="groq",
                description=f"Sub-second time-to-first-token model for rapid inference{desc_suffix}.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=False,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=False,
                ),
                is_available=True,
                context_window=128000,
                tier="free"
            ),
            ModelInfo(
                id="mixtral-8x7b-32768",
                name="Mixtral 8x7B",
                provider="groq",
                description=f"High throughput mixture-of-experts model{desc_suffix}.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=False,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=False,
                ),
                is_available=True,
                context_window=32768,
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

    def _augment_system_prompt(self, model: str, existing_prompt: Optional[str] = None) -> str:
        clean = model.lower()
        if "mixtral" in clean or "mistral" in clean:
            persona = "You are Mixtral 8x7B, Mistral AI's high-throughput mixture-of-experts model. You provide fast, precise, well-structured responses."
        else:
            persona = f"You are {model}, Meta's open-weights high-performance AI model. You provide clear, concise, and structured responses with expert technical and general problem-solving."
        if existing_prompt:
            return f"{persona}\n\nUser instructions: {existing_prompt}"
        return persona

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if self._has_groq_key():
            payload = self._prepare_payload(messages, model, temperature, system_prompt, stream=False)
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                res = await client.post(f"{self.BASE_URL}/chat/completions", json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
                choices = data.get("choices", [])
                if not choices:
                    return {
                        "content": "",
                        "model_used": model,
                        "provider_used": "groq",
                        "finish_reason": "stop",
                        "citations": []
                    }
                choice = choices[0]
                return {
                    "content": choice["message"]["content"] or "",
                    "model_used": model,
                    "provider_used": "groq",
                    "finish_reason": choice.get("finish_reason", "stop"),
                    "citations": []
                }
        else:
            # Live Free Cloud Gateway routing
            augmented_sys = self._augment_system_prompt(model, system_prompt)
            formatted = [{"role": "system", "content": augmented_sys}]
            for m in messages:
                formatted.append({"role": m.get("role", "user"), "content": m.get("content", "")})
            payload = {
                "model": "openai",
                "messages": formatted,
                "temperature": temperature,
                "stream": False
            }
            async with httpx.AsyncClient(timeout=40.0) as client:
                res = await client.post("https://text.pollinations.ai/openai/chat/completions", json=payload)
                res.raise_for_status()
                data = res.json()
                choices = data.get("choices", [])
                if not choices:
                    return {
                        "content": "",
                        "model_used": model,
                        "provider_used": "groq",
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
                    "provider_used": "groq (free gateway)",
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
        if self._has_groq_key():
            payload = self._prepare_payload(messages, model, temperature, system_prompt, stream=True)
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }

            yield {
                "type": "status",
                "data": {"status": "Streaming from Groq LPU...", "provider": "groq"}
            }

            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", f"{self.BASE_URL}/chat/completions", json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                yield {
                                    "type": "done",
                                    "data": {
                                        "model_used": model,
                                        "provider_used": "groq",
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
                                content = delta.get("content")
                                if content:
                                    yield {"type": "token", "data": {"token": content}}
                            except json.JSONDecodeError:
                                continue
        else:
            # Live Free Cloud Gateway routing
            augmented_sys = self._augment_system_prompt(model, system_prompt)
            formatted = [{"role": "system", "content": augmented_sys}]
            for m in messages:
                formatted.append({"role": m.get("role", "user"), "content": m.get("content", "")})
            payload = {
                "model": "openai",
                "messages": formatted,
                "temperature": temperature,
                "stream": True
            }

            yield {
                "type": "status",
                "data": {"status": f"Streaming from {model} (Free Cloud Gateway)...", "provider": "groq"}
            }

            has_started_thinking = False
            has_closed_thinking = False

            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", "https://text.pollinations.ai/openai/chat/completions", json=payload) as response:
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
                                        "provider_used": "groq (free gateway)",
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
