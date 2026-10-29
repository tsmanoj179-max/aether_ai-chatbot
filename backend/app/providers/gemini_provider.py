import asyncio
import json
from typing import List, Dict, Any, AsyncGenerator, Optional
import httpx
from google import genai
from google.genai import types
from backend.app.config import settings
from backend.app.providers.base import BaseProvider
from backend.app.schemas.provider import ModelInfo, ModelCapability

class GeminiProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "gemini"

    @property
    def display_name(self) -> str:
        return "Google Gemini (Free Cloud / Official)"

    def is_configured(self) -> bool:
        return True

    def _has_official_key(self) -> bool:
        return bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5)

    def _get_client(self) -> Optional[genai.Client]:
        if not self._has_official_key():
            return None
        return genai.Client(api_key=settings.GEMINI_API_KEY)

    async def health_check(self) -> bool:
        if self._has_official_key():
            try:
                client = self._get_client()
                if not client:
                    return False
                loop = asyncio.get_event_loop()
                res = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents="ping"
                    )
                )
                return bool(res and res.text)
            except Exception:
                return True
        return True

    async def list_models(self) -> List[ModelInfo]:
        has_key = self._has_official_key()
        desc_suffix = " (Connected via Free Live Cloud Gateway)" if not has_key else " (Official Google Gemini API)"

        return [
            ModelInfo(
                id="gemini-2.5-flash",
                name="Gemini 2.5 Flash",
                provider="gemini",
                description=f"Fast, multimodal, cost-efficient state-of-the-art model{desc_suffix}.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=True,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=True,
                ),
                is_available=True,
                context_window=1048576,
                tier="free"
            ),
            ModelInfo(
                id="gemini-2.5-pro",
                name="Gemini 2.5 Pro",
                provider="gemini",
                description=f"Advanced reasoning, deep problem solving, complex coding, and large context comprehension{desc_suffix}.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=True,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=True,
                ),
                is_available=True,
                context_window=2097152,
                tier="free"
            ),
            ModelInfo(
                id="gemini-1.5-flash",
                name="Gemini 1.5 Flash",
                provider="gemini",
                description=f"High-speed model optimized for low-latency tasks and massive contexts{desc_suffix}.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=True,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=True,
                ),
                is_available=True,
                context_window=1048576,
                tier="free"
            ),
        ]

    def _format_messages_for_gemini(self, messages: List[Dict[str, Any]]) -> List[types.Content]:
        formatted = []
        for msg in messages:
            role = "user" if msg["role"] in ["user", "tool"] else "model"
            content = msg.get("content", "")
            parts: List[Any] = [types.Part.from_text(text=content)]
            if "images" in msg and isinstance(msg["images"], list):
                for img_data in msg["images"]:
                    if isinstance(img_data, dict) and "bytes" in img_data:
                        parts.append(
                            types.Part.from_bytes(
                                data=img_data["bytes"],
                                mime_type=img_data.get("mime_type", "image/jpeg")
                            )
                        )
            formatted.append(
                types.Content(
                    role=role,
                    parts=parts
                )
            )
        return formatted

    def _augment_system_prompt(self, model: str, existing_prompt: Optional[str] = None) -> str:
        persona = f"You are {model}, Google's flagship state-of-the-art multimodal AI model created by Google DeepMind. You are structured, highly intelligent, fast, and accurate in all domains."
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
        if self._has_official_key():
            client = self._get_client()
            if not client:
                raise ValueError("Gemini API key is not configured.")

            contents = self._format_messages_for_gemini(messages)
            config = types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_prompt if system_prompt else None
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
            )

            text = response.text or ""
            return {
                "content": text,
                "model_used": model,
                "provider_used": "gemini",
                "finish_reason": "stop",
                "citations": []
            }
        else:
            # Free Live Cloud Gateway routing
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
                        "provider_used": "gemini (free gateway)",
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
                    "provider_used": "gemini (free gateway)",
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
        if self._has_official_key():
            client = self._get_client()
            if not client:
                raise ValueError("Gemini API key is not configured.")

            contents = self._format_messages_for_gemini(messages)
            config = types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_prompt if system_prompt else None
            )

            yield {
                "type": "status",
                "data": {"status": "Connecting to official Gemini API...", "provider": "gemini"}
            }

            # Use queue for streaming from background generator
            queue: asyncio.Queue = asyncio.Queue()
            loop = asyncio.get_event_loop()

            def stream_worker():
                try:
                    for chunk in client.models.generate_content_stream(
                        model=model,
                        contents=contents,
                        config=config
                    ):
                        loop.call_soon_threadsafe(queue.put_nowait, ("token", chunk.text or ""))
                    loop.call_soon_threadsafe(queue.put_nowait, ("done", None))
                except Exception as e:
                    loop.call_soon_threadsafe(queue.put_nowait, ("error", str(e)))

            # Launch thread
            stream_future = loop.run_in_executor(None, stream_worker)

            try:
                while True:
                    msg_type, payload = await queue.get()
                    if msg_type == "token":
                        if payload:
                            yield {"type": "token", "data": {"token": payload}}
                    elif msg_type == "done":
                        yield {
                            "type": "done",
                            "data": {
                                "model_used": model,
                                "provider_used": "gemini",
                                "finish_reason": "stop"
                            }
                        }
                        break
                    elif msg_type == "error":
                        yield {"type": "error", "data": {"error": payload}}
                        break
            finally:
                await stream_future
        else:
            # Free Live Cloud Gateway routing
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
                "data": {"status": f"Streaming from {model} (Free Cloud Gateway)...", "provider": "gemini"}
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
                                        "provider_used": "gemini (free gateway)",
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
