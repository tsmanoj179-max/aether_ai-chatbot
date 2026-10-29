import asyncio
import re
from typing import List, Dict, Any, AsyncGenerator, Optional
from backend.app.providers.base import BaseProvider
from backend.app.schemas.provider import ModelInfo, ModelCapability

class MockProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "mock"

    @property
    def display_name(self) -> str:
        return "AetherAI Deterministic Simulator"

    def is_configured(self) -> bool:
        return True

    async def health_check(self) -> bool:
        return True

    async def list_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                id="aether-mock-omni",
                name="Aether Omni (Simulated)",
                provider="mock",
                description="General-purpose high intelligence simulated model supporting multimodal inputs, tool execution, and deep synthesis.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=True,
                    tool_calling=True,
                    structured_output=True,
                    web_search=True,
                    deep_research=True,
                ),
                is_available=True,
                context_window=32768,
                tier="mock"
            ),
            ModelInfo(
                id="aether-mock-code",
                name="Aether Code (Simulated)",
                provider="mock",
                description="Simulated coding assistant optimized for algorithm design, refactoring, and full-stack debugging.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=False,
                    tool_calling=True,
                    structured_output=True,
                    web_search=False,
                    deep_research=False,
                ),
                is_available=True,
                context_window=65536,
                tier="mock"
            ),
            ModelInfo(
                id="aether-mock-fast",
                name="Aether Instant (Simulated)",
                provider="mock",
                description="Ultra-low latency simulated model for rapid query testing.",
                capabilities=ModelCapability(
                    streaming=True,
                    vision=False,
                    tool_calling=False,
                    structured_output=True,
                    web_search=False,
                    deep_research=False,
                ),
                is_available=True,
                context_window=16384,
                tier="mock"
            ),
        ]

    def _synthesize_mock_response(
        self,
        last_message: str,
        model: str,
        system_prompt: Optional[str] = None
    ) -> str:
        msg_lower = last_message.lower().strip()

        # Simulated banner with Thinking Process
        thought = (
            "<think>\n"
            "1. Deconstruct user intent and operational context.\n"
            "2. Evaluate active workspace persona and safety boundaries.\n"
            "3. Synthesize structured answer with typed code or verifiable evidence.\n"
            "4. Verify zero hallucination of external API credentials.\n"
            "</think>\n\n"
        )

        sim_header = "> [!NOTE]\n> **Simulated Response**: Running in deterministic demonstration mode without requiring external API keys.\n\n"

        if any(w in msg_lower for w in ["html", "ui", "component", "button", "card", "visual"]):
            return thought + sim_header + (
                "Here is an interactive modern component designed for your workspace. You can click **Canvas** on this code block to preview it live side-by-side:\n\n"
                "```html\n"
                "<!DOCTYPE html>\n"
                "<html>\n"
                "<head>\n"
                "  <style>\n"
                "    body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; margin: 0; }\n"
                "    .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; max-width: 380px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }\n"
                "    .title { font-size: 16px; font-weight: 700; color: #818cf8; margin-bottom: 8px; }\n"
                "    .desc { font-size: 13px; color: #94a3b8; line-height: 1.5; margin-bottom: 16px; }\n"
                "    .btn { background: #6366f1; color: white; border: none; padding: 8px 16px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; transition: 0.2s; }\n"
                "    .btn:hover { background: #4f46e5; }\n"
                "  </style>\n"
                "</head>\n"
                "<body>\n"
                "  <div class=\"card\">\n"
                "    <div class=\"title\">AetherAI Canvas Studio</div>\n"
                "    <div class=\"desc\">Interactive side-by-side artifact renderer supporting real-time HTML, CSS, SVG, and code execution.</div>\n"
                "    <button class=\"btn\" onclick=\"alert('AetherAI Canvas Interactivity Active!')\">Explore Canvas</button>\n"
                "  </div>\n"
                "</body>\n"
                "</html>\n"
                "```\n\n"
                "### Canvas Capabilities:\n"
                "- **Live Sandbox**: Renders in an isolated sandbox iframe.\n"
                "- **Side-by-Side**: Keep conversing while testing components.\n"
                "- **Instant Export**: Download as a file anytime."
            )

        if any(w in msg_lower for w in ["code", "python", "javascript", "function", "class", "algorithm", "debug"]):
            return thought + sim_header + (
                "Here is an optimized implementation tailored to your requirements:\n\n"
                "```python\n"
                "from typing import List, Dict, Any\n"
                "import asyncio\n\n"
                "class DataPipeline:\n"
                "    \"\"\"High-performance concurrent stream processor.\"\"\"\n"
                "    def __init__(self, batch_size: int = 50):\n"
                "        self.batch_size = batch_size\n"
                "        self.records: List[Dict[str, Any]] = []\n\n"
                "    async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:\n"
                "        # Clean and enrich input payload\n"
                "        transformed = {k: v.strip() if isinstance(v, str) else v for k, v in item.items()}\n"
                "        transformed[\"processed\"] = True\n"
                "        return transformed\n\n"
                "    async def flush(self) -> int:\n"
                "        count = len(self.records)\n"
                "        self.records.clear()\n"
                "        return count\n"
                "```\n\n"
                "### Key Architectural Features:\n"
                "- **Strong Type Annotations**: Clear data contracts via `typing`.\n"
                "- **Asynchronous Execution**: Non-blocking I/O operations.\n"
                "- **Resource Containment**: Memory bounded with batch flushes.\n"
                "- *Tip*: Click the **Canvas** button above to open this in your side-by-side workspace."
            )

        if any(w in msg_lower for w in ["research", "search", "latest", "news", "trend", "report"]):
            return thought + sim_header + (
                "### Comparative Research Matrix\n\n"
                "| Architecture Strategy | Throughput | Local Memory Overhead | Hardware Prerequisite |\n"
                "| :--- | :--- | :--- | :--- |\n"
                "| **Cloud API (Gemini/Groq)** | 120-250 tok/s | ~50 MB RAM | Standard CPU |\n"
                "| **Local Ollama (Quantized)** | 15-40 tok/s | 4-8 GB RAM | 8+ Core CPU or GPU |\n"
                "| **Deterministic Simulator** | >500 tok/s | Zero footprint | Any hardware |\n\n"
                "### Synthesized Insights:\n"
                "1. **Core Consensus**: Distributed multi-agent systems and retrieval-augmented generation have converged into unified execution workspaces.\n"
                "2. **Primary Challenges**: Latency overhead in complex tool calling chains and memory drift over extended multi-turn dialogs.\n"
                "3. **Recommended Actions**: Implement bounded exponential backoff on rate limits, partition working memory into ephemeral scratchpads and persistent preferences, and maintain strict token budgeting.\n\n"
                "**Evidence Sources**:\n"
                "- *Source 1: AetherAI Autonomous Systems Whitepaper (2026)*\n"
                "- *Source 2: Contemporary Standards for RAG Architectures*"
            )

        if any(w in msg_lower for w in ["who are you", "what are you", "what can you do", "help", "hello", "hi"]):
            return sim_header + (
                "Hello! I am **AetherAI**, an intelligent, modular AI workspace designed for deep work, coding assistance, document intelligence, and multi-provider orchestration.\n\n"
                "### What I can do for you:\n"
                "- 💬 **Conversational AI**: Multi-turn dialogue with streaming and full history persistence.\n"
                "- 🧠 **Document Intelligence (RAG)**: Ingest PDFs, Word docs, CSVs, and codebases with localized vector search.\n"
                "- 🌐 **Live Web Research**: Sourced research reports with transparent citations.\n"
                "- 🛠️ **Modular Tool Registry**: Calculator, date/time utilities, Python data analysis, and document retrieval.\n"
                "- ⚙️ **Multi-Provider Support**: Seamlessly switch between Google Gemini, Groq, Ollama, OpenAI-compatible backends, and this deterministic simulator.\n\n"
                "How would you like to proceed today?"
            )

        # Default helpful synthesis
        return sim_header + (
            f"I have analyzed your query: *\"{last_message}\"*.\n\n"
            "Here is the synthesized overview:\n\n"
            "- **Direct Answer**: The system is fully operational and responsive to your request.\n"
            "- **Design Considerations**: All operations are contained within the local sandbox, preserving safety and predictable performance.\n"
            "- **Next Steps**: You can configure live API keys in the Settings modal (Gemini, Groq, or OpenAI) to switch from simulation to live cloud inference at any time."
        )

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        last_message = messages[-1].get("content", "") if messages else "Hello"
        content = self._synthesize_mock_response(last_message, model, system_prompt)
        return {
            "content": content,
            "model_used": model,
            "provider_used": "mock",
            "finish_reason": "stop",
            "citations": [
                {
                    "title": "AetherAI Documentation",
                    "url": "https://aetherai.local/docs",
                    "snippet": "Deterministic demonstration provider running in memory."
                }
            ]
        }

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        last_message = messages[-1].get("content", "") if messages else "Hello"
        content = self._synthesize_mock_response(last_message, model, system_prompt)

        # Emit simulated status update
        yield {
            "type": "status",
            "data": {"status": "Synthesizing response...", "provider": "mock"}
        }
        await asyncio.sleep(0.04)

        # Chunk the output into natural words/tokens
        words = re.findall(r'\S+|\n|\s+', content)
        for i in range(0, len(words), 3):
            chunk = "".join(words[i:i+3])
            yield {
                "type": "token",
                "data": {"token": chunk}
            }
            # Fast, smooth simulation delay
            await asyncio.sleep(0.02)

        # Emit citation if relevant
        yield {
            "type": "citation",
            "data": {
                "title": "AetherAI Local System Runtime",
                "url": "local://system-status",
                "snippet": "Local sandbox operational. Zero network leaks."
            }
        }

        yield {
            "type": "done",
            "data": {
                "model_used": model,
                "provider_used": "mock",
                "finish_reason": "stop"
            }
        }
