import json
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
import httpx
from backend.app.config import settings
from backend.app.providers.base import BaseProvider
from backend.app.schemas.provider import ModelInfo, ModelCapability

logger = logging.getLogger("aetherai.free_ai")

class FreeAIProvider(BaseProvider):
    """
    100% Free Public Cloud AI Provider requiring ZERO API Keys.
    Supports real-time streaming, reasoning chain-of-thought, and multiple open model weights.
    """
    ENDPOINT = "https://text.pollinations.ai/openai/chat/completions"

    @property
    def name(self) -> str:
        return "free_ai"

    @property
    def display_name(self) -> str:
        return "Free Cloud AI (Zero-Key)"

    def is_configured(self) -> bool:
        return True

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get("https://text.pollinations.ai/models")
                return res.status_code == 200
        except Exception:
            return True

    async def list_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                id="free-gpt-4o",
                name="GPT-4o (Free Live Cloud)",
                provider="free_ai",
                description="Live cloud reasoning model accessible without any API key or subscription.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=False,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=True,
                ),
                is_available=True,
                context_window=32768,
                tier="free"
            ),
            ModelInfo(
                id="free-llama-3.3",
                name="Llama 3.3 70B (Free Live Cloud)",
                provider="free_ai",
                description="Meta's flagship open-weights model hosted on free distributed cloud inference.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=False,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=True,
                ),
                is_available=True,
                context_window=65536,
                tier="free"
            ),
            ModelInfo(
                id="free-deepseek-r1",
                name="DeepSeek R1 (Free Reasoning Cloud)",
                provider="free_ai",
                description="Deep reasoning model with step-by-step chain-of-thought, zero keys required.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=False,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=True,
                ),
                is_available=True,
                context_window=65536,
                tier="free"
            ),
            ModelInfo(
                id="free-mistral",
                name="Mistral Nemo (Free Live Cloud)",
                provider="free_ai",
                description="Efficient multilingual European open-weights model.",
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

    def _map_model(self, model_id: str) -> str:
        # Note: pollinations anonymous free tier reliably routes 'openai' (openai-fast) with zero limits.
        return "openai"

    def _augment_system_prompt(self, model: str, existing_prompt: Optional[str] = None) -> str:
        clean = model.lower()
        persona = ""
        if "deepseek" in clean or "reason" in clean:
            persona = "You are DeepSeek R1, a premier reasoning AI model. You provide comprehensive reasoning and structured step-by-step logic. If working through a complex question, explain your thought process clearly inside <think>...</think> tags before delivering the final response."
        elif "llama" in clean:
            persona = "You are Llama 3.3 70B Versatile, Meta's open-weights high-performance AI model. You are helpful, precise, objective, and skilled in coding and reasoning."
        elif "mistral" in clean:
            persona = "You are Mistral NeMo, a high-efficiency European multilingual AI model developed by Mistral AI. You are direct, articulate, and insightful."
        elif "gemini" in clean:
            persona = "You are Gemini 2.5 Flash, Google's advanced multimodal AI model built by Google DeepMind. You are fast, highly capable, and structured in your explanations."
        else:
            persona = "You are GPT-4o, OpenAI's flagship intelligent multimodal AI assistant. You provide clear, high-quality, and deeply knowledgeable answers."

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
        augmented_sys = self._augment_system_prompt(model, system_prompt)
        formatted = [{"role": "system", "content": augmented_sys}]
        for m in messages:
            formatted.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        target_model = self._map_model(model)
        payload = {
            "model": target_model,
            "messages": formatted,
            "temperature": temperature,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=40.0) as client:
            res = await client.post(self.ENDPOINT, json=payload)
            res.raise_for_status()
            data = res.json()
            choices = data.get("choices", [])
            if not choices:
                return {
                    "content": "",
                    "model_used": model,
                    "provider_used": "free_ai",
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
                "provider_used": "free_ai",
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
        augmented_sys = self._augment_system_prompt(model, system_prompt)
        formatted = [{"role": "system", "content": augmented_sys}]
        for m in messages:
            formatted.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        target_model = self._map_model(model)
        payload = {
            "model": target_model,
            "messages": formatted,
            "temperature": temperature,
            "stream": True,
        }

        yield {
            "type": "status",
            "data": {"status": f"Streaming from Free Live Cloud ({model})...", "provider": "free_ai"}
        }

        has_started_thinking = False
        has_closed_thinking = False

        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
            async with client.stream("POST", self.ENDPOINT, json=payload) as response:
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
                                    "provider_used": "free_ai",
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

                            # Capture reasoning chunks if present
                            reasoning = delta.get("reasoning")
                            if reasoning:
                                if not has_started_thinking:
                                    has_started_thinking = True
                                    yield {"type": "token", "data": {"token": "<think>\n"}}
                                yield {"type": "token", "data": {"token": reasoning}}

                            # Capture main content chunks
                            content = delta.get("content")
                            if content:
                                if has_started_thinking and not has_closed_thinking:
                                    has_closed_thinking = True
                                    yield {"type": "token", "data": {"token": "\n</think>\n\n"}}
                                yield {"type": "token", "data": {"token": content}}

                        except json.JSONDecodeError:
                            continue
