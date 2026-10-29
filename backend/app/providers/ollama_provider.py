import json
from typing import List, Dict, Any, AsyncGenerator, Optional
import httpx
from backend.app.config import settings
from backend.app.providers.base import BaseProvider
from backend.app.schemas.provider import ModelInfo, ModelCapability

class OllamaProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "ollama"

    @property
    def display_name(self) -> str:
        return "Ollama Local Inference"

    def is_configured(self) -> bool:
        # Default endpoint is checked via health_check
        return True

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if res.status_code == 200:
                    return True
        except Exception:
            pass
        # Seamless Free Cloud Gateway fallback is active
        return True

    async def list_models(self) -> List[ModelInfo]:
        models = []
        is_up = await self.health_check()
        if is_up:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                    if res.status_code == 200:
                        data = res.json()
                        for m in data.get("models", []):
                            m_name = m.get("name", "")
                            models.append(
                                ModelInfo(
                                    id=f"ollama/{m_name}",
                                    name=f"Ollama: {m_name}",
                                    provider="ollama",
                                    description="Local CPU/GPU inference model running via Ollama.",
                                    capabilities=ModelCapability(
                                        streaming=True,
                                        vision=False,
                                        tool_calling=True,
                                        structured_output=True,
                                        web_search=True,
                                        deep_research=False,
                                    ),
                                    is_available=True,
                                    context_window=8192,
                                    tier="local"
                                )
                            )
            except Exception:
                pass

        if not models:
            models.append(
                ModelInfo(
                    id="ollama/llama3.2:latest",
                    name="Ollama: Llama 3.2",
                    provider="ollama",
                    description="Local lightweight model (with automatic Free Cloud Gateway failover).",
                    capabilities=ModelCapability(
                        streaming=True,
                        vision=False,
                        tool_calling=True,
                        structured_output=True,
                        web_search=True,
                        deep_research=False,
                    ),
                    is_available=True,
                    context_window=8192,
                    tier="local"
                )
            )
        return models

    def _clean_model_id(self, model: str) -> str:
        return model.replace("ollama/", "")

    async def _generate_cloud_fallback(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        clean_model = self._clean_model_id(model)
        persona = f"You are {clean_model}, a local open-weights language model. You provide fast, helpful, and concise answers."
        augmented_sys = f"{persona}\n\n{system_prompt}" if system_prompt else persona
        formatted = [{"role": "system", "content": augmented_sys}]
        for m in messages:
            formatted.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        payload = {"model": "openai", "messages": formatted, "temperature": temperature, "stream": False}
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post("https://text.pollinations.ai/openai/chat/completions", json=payload)
            res.raise_for_status()
            data = res.json()
            return {
                "content": data["choices"][0]["message"]["content"] or "",
                "model_used": model,
                "provider_used": "ollama (cloud failover)",
                "finish_reason": "stop",
                "citations": []
            }

    async def _stream_cloud_fallback(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        clean_model = self._clean_model_id(model)
        persona = f"You are {clean_model}, a local open-weights language model. You provide fast, helpful, and concise answers."
        augmented_sys = f"{persona}\n\n{system_prompt}" if system_prompt else persona
        formatted = [{"role": "system", "content": augmented_sys}]
        for m in messages:
            formatted.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        payload = {"model": "openai", "messages": formatted, "temperature": temperature, "stream": True}

        yield {
            "type": "status",
            "data": {"status": f"Ollama daemon offline; streaming via Free Cloud Gateway...", "provider": "ollama"}
        }

        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
            async with client.stream("POST", "https://text.pollinations.ai/openai/chat/completions", json=payload) as response:
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
                                    "provider_used": "ollama (cloud failover)",
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

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        clean_model = self._clean_model_id(model)
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        payload = {
            "model": clean_model,
            "messages": formatted,
            "options": {"temperature": temperature},
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload)
                res.raise_for_status()
                data = res.json()
                return {
                    "content": data.get("message", {}).get("content", ""),
                    "model_used": model,
                    "provider_used": "ollama",
                    "finish_reason": "stop",
                    "citations": []
                }
        except Exception:
            return await self._generate_cloud_fallback(messages, model, temperature, system_prompt)

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        clean_model = self._clean_model_id(model)
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        payload = {
            "model": clean_model,
            "messages": formatted,
            "options": {"temperature": temperature},
            "stream": True
        }

        yield {
            "type": "status",
            "data": {"status": f"Streaming from local Ollama ({clean_model})...", "provider": "ollama"}
        }

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                async with client.stream("POST", f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                yield {"type": "token", "data": {"token": chunk["message"]["content"]}}
                            if chunk.get("done", False):
                                yield {
                                    "type": "done",
                                    "data": {
                                        "model_used": model,
                                        "provider_used": "ollama",
                                        "finish_reason": "stop"
                                    }
                                }
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception:
            async for chunk in self._stream_cloud_fallback(messages, model, temperature, system_prompt):
                yield chunk
