import asyncio
import os
import sys
import uuid
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme
from rich.rule import Rule

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from backend.app.config import settings
from backend.app.database import SessionLocal, init_db
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.providers.registry import provider_registry
from backend.app.services.document_service import document_service
from backend.app.services.search_service import search_service
from backend.app.services.research_service import research_service
from backend.app.services.tool_registry import tool_registry
from backend.app.services.memory_service import memory_service
from backend.app.services.image_service import image_service

# Custom Rich theme
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green",
    "accent": "bold magenta",
    "brand": "bold cyan",
})

console = Console(theme=custom_theme, legacy_windows=False)

BANNER = r"""[bold cyan]
     █████╗ ███████╗████████╗██╗  ██╗███████╗██████╗  █████╗ ██╗
    ██╔══██╗██╔════╝╚══██╔══╝██║  ██║██╔════╝██╔══██╗██╔══██╗██║
    ███████║█████╗     ██║   ███████║█████╗  ██████╔╝███████║██║
    ██╔══██║██╔══╝     ██║   ██╔══██║██╔══╝  ██╔══██╗██╔══██║██║
    ██║  ██║███████╗   ██║   ██║  ██║███████╗██║  ██║██║  ██║██║
    ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝[/bold cyan]
    [dim]AetherAI CLI • Intelligent Multi-Provider Terminal Workspace[/dim]
"""

PERSONA_PROMPTS = {
    "general": "You are AetherAI, a sophisticated, helpful, precise, and proactive AI workspace assistant.",
    "coder": "You are an expert Principal Software Architect and Senior Engineer. You write clean, robust, modern, production-grade code with meticulous error handling, type safety, and clear comments.",
    "researcher": "You are a Senior Research Scientist and Academic Analyst. You synthesize complex literature, provide rigorous reasoning, cite sources meticulously, and evaluate evidence objectively.",
    "analyst": "You are a Principal Data Analyst and Business Intelligence Expert. You analyze datasets, formulate data-driven insights, extract actionable metrics, and highlight risks.",
    "writer": "You are an award-winning Editor and Technical Writer. You craft articulate, engaging, well-structured prose, documentation, and executive summaries with elegant phrasing."
}

SLASH_COMMANDS = [
    "/help", "/models", "/model", "/persona", "/search", "/research",
    "/image", "/analyze", "/file", "/tool", "/memory", "/history", "/clear",
    "/new", "/save", "/status", "/exit", "/quit"
]

prompt_style = Style.from_dict({
    'prompt': 'ansicyan bold',
    'model': 'ansimagenta',
})


class AetherCLI:
    def __init__(self, model: Optional[str] = None, persona: str = "general"):
        init_db()
        self.model = model or settings.DEFAULT_MODEL
        self.persona = persona if persona in PERSONA_PROMPTS else "general"
        self.conversation_id = str(uuid.uuid4())
        self.messages: List[Dict[str, Any]] = []
        self.active_documents_text: List[str] = []
        self._init_db_conversation()
        self.session = None

    def _get_input(self, prompt_text: str) -> str:
        if self.session is None:
            try:
                history_file = os.path.expanduser("~/.aetherai_history")
                self.session = PromptSession(
                    history=FileHistory(history_file),
                    completer=WordCompleter(SLASH_COMMANDS + [
                        "gemini-2.5-flash", "gemini-2.5-pro", "llama-3.3-70b-versatile",
                        "gpt-4o", "gpt-4o-mini", "free-deepseek-r1", "free-mistral",
                        "free-llama-3.3", "free-gpt-4o", "ollama/llama3.2:latest"
                    ], ignore_case=True)
                )
            except Exception:
                self.session = False

        if self.session:
            try:
                return self.session.prompt(prompt_text, style=prompt_style)
            except Exception:
                pass
        return input(prompt_text)

    def _init_db_conversation(self):
        try:
            db = SessionLocal()
            conv = Conversation(
                id=self.conversation_id,
                title=f"CLI Session ({self.model})",
                folder="cli",
                model_id=self.model,
                system_prompt=PERSONA_PROMPTS.get(self.persona, "")
            )
            db.add(conv)
            db.commit()
            db.close()
        except Exception:
            pass

    def _save_message_to_db(self, role: str, content: str, model_used: Optional[str] = None):
        try:
            db = SessionLocal()
            msg = Message(
                conversation_id=self.conversation_id,
                role=role,
                content=content,
                model_used=model_used or self.model,
                provider_used="cli"
            )
            db.add(msg)
            # Update conversation title if first user message
            if role == "user" and len(self.messages) <= 2:
                conv = db.query(Conversation).filter(Conversation.id == self.conversation_id).first()
                if conv:
                    title = content.strip().replace("\n", " ")[:60]
                    if len(content) > 60:
                        title += "..."
                    conv.title = title
            db.commit()
            db.close()
        except Exception:
            pass

    def print_banner(self):
        console.print(BANNER)
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("[bold cyan]Model:[/bold cyan]", f"[bold magenta]{self.model}[/bold magenta] (0-Key Ready)")
        table.add_row("[bold cyan]Persona:[/bold cyan]", f"[green]{self.persona.capitalize()}[/green]")
        table.add_row("[bold cyan]Session ID:[/bold cyan]", f"[dim]{self.conversation_id[:8]}...[/dim]")
        table.add_row("[bold cyan]Quick Help:[/bold cyan]", "[dim]Type [bold]/help[/bold] for commands, [bold]/exit[/bold] to quit[/dim]")
        console.print(Panel(table, border_style="cyan", title="[bold]AetherAI Active Environment[/bold]"))
        console.print()

    async def handle_slash_command(self, cmd: str) -> bool:
        """Returns True if command handled, False to continue or exit."""
        parts = cmd.strip().split(maxsplit=1)
        action = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if action in ["/exit", "/quit"]:
            console.print("[dim cyan]Goodbye! Session saved to AetherAI history.[/dim cyan]")
            return False

        if action == "/help":
            self.show_help()
            return True

        if action == "/models":
            await self.show_models()
            return True

        if action == "/model":
            if not arg:
                console.print(f"[warning]Current model is:[/warning] [bold magenta]{self.model}[/bold magenta]")
                console.print("[info]Use [bold]/model <id>[/bold] to switch, or [bold]/models[/bold] to list.[/info]")
            else:
                self.model = arg
                console.print(f"[success]Active model switched to:[/success] [bold magenta]{self.model}[/bold magenta]")
            return True

        if action == "/persona":
            if not arg or arg not in PERSONA_PROMPTS:
                console.print(f"[warning]Available personas:[/warning] {', '.join(PERSONA_PROMPTS.keys())}")
            else:
                self.persona = arg
                console.print(f"[success]Active persona switched to:[/success] [green]{self.persona.capitalize()}[/green]")
            return True

        if action in ["/clear", "/new"]:
            self.conversation_id = str(uuid.uuid4())
            self.messages.clear()
            self.active_documents_text.clear()
            self._init_db_conversation()
            console.print(f"[success]New conversation started![/success] [dim]Session ID: {self.conversation_id[:8]}[/dim]")
            return True

        if action == "/history":
            self.show_history()
            return True

        if action == "/file":
            if not arg:
                console.print("[danger]Usage: /file <path/to/file>[/danger]")
            else:
                await self.load_file(arg)
            return True

        if action == "/image":
            if not arg:
                console.print("[danger]Usage: /image <prompt> [--style photorealistic|anime|cyberpunk|3d_render|oil_painting] [--aspect 1:1|16:9|9:16][/danger]")
            else:
                await self.generate_image_cmd(arg)
            return True

        if action == "/analyze":
            if not arg:
                console.print("[danger]Usage: /analyze <path/to/image>[/danger]")
            else:
                await self.analyze_image_cmd(arg)
            return True

        if action == "/search":
            if not arg:
                console.print("[danger]Usage: /search <query>[/danger]")
            else:
                await self.execute_search(arg)
            return True

        if action == "/research":
            if not arg:
                console.print("[danger]Usage: /research <topic>[/danger]")
            else:
                await self.execute_deep_research(arg)
            return True

        if action == "/tool":
            if not arg:
                console.print("[danger]Usage: /tool <tool_name> [args][/danger]")
                console.print("[info]Available tools: calculator, datetime, dataset_summary[/info]")
            else:
                await self.execute_tool(arg)
            return True

        if action == "/memory":
            await self.handle_memory(arg)
            return True

        if action == "/save":
            self.save_conversation(arg)
            return True

        if action == "/status":
            await self.show_status()
            return True

        console.print(f"[danger]Unknown command:[/danger] {action}. Type [bold]/help[/bold] for available commands.")
        return True

    def show_help(self):
        table = Table(title="AetherAI CLI Command Reference", border_style="cyan")
        table.add_column("Command", style="bold cyan")
        table.add_column("Description", style="white")
        table.add_column("Example", style="dim")

        table.add_row("/models", "List all available AI models & provider tiers", "/models")
        table.add_row("/model <id>", "Switch the active language model", "/model gemini-2.5-flash")
        table.add_row("/persona <name>", "Switch role (general, coder, researcher, analyst, writer)", "/persona coder")
        table.add_row("/search <query>", "Execute a live web search with citations", "/search quantum computing breakthroughs")
        table.add_row("/research <topic>", "Perform deep multi-step research synthesis", "/research AI agent architecture 2026")
        table.add_row("/image <prompt>", "Generate high-res artwork via FLUX.1 neural engine", "/image cybernetic owl in rain --style cyberpunk")
        table.add_row("/analyze <path>", "Analyze image properties, colors & multimodal scene", "/analyze photo.jpg")
        table.add_row("/file <path>", "Ingest a local document (PDF, TXT, DOCX, Code, CSV)", "/file data/report.pdf")
        table.add_row("/tool <name> [args]", "Execute an AST tool (calculator, datetime)", "/tool calculator 17 * 19")
        table.add_row("/memory [list|add|clear]", "Inspect or save personalization facts", "/memory add User prefers Python 3.12")
        table.add_row("/history", "Display current session conversation turns", "/history")
        table.add_row("/clear or /new", "Reset context and start a clean session", "/new")
        table.add_row("/save [path]", "Export conversation as a formatted Markdown file", "/save my_notes.md")
        table.add_row("/status", "Display provider health and database statistics", "/status")
        table.add_row("/exit or /quit", "Save session and exit terminal REPL", "/exit")

        console.print(table)

    async def show_models(self):
        models = await provider_registry.get_all_models()
        table = Table(title="Available AI Models (All Configured & Ready)", border_style="cyan")
        table.add_column("Model ID", style="bold cyan")
        table.add_column("Name", style="white")
        table.add_column("Provider", style="magenta")
        table.add_column("Context", style="yellow")
        table.add_column("Tier", style="green")
        table.add_column("Active", style="bold")

        for m in models:
            is_active = "[bold green]★ Current[/bold green]" if m.id == self.model else "[dim]Ready[/dim]"
            context_str = f"{(m.context_window / 1024):.0f}k"
            table.add_row(m.id, m.name, m.provider, context_str, m.tier.upper(), is_active)

        console.print(table)

    async def show_status(self):
        providers = await provider_registry.get_providers_status()
        table = Table(title="AetherAI System & Provider Status", border_style="cyan")
        table.add_column("Provider", style="bold white")
        table.add_column("Configured", style="green")
        table.add_column("Available", style="cyan")
        table.add_column("Models Loaded", style="yellow")

        for p in providers:
            cfg = "[green]Yes[/green]" if p.is_configured else "[red]No[/red]"
            avail = "[green]Online[/green]" if p.is_available else "[red]Offline[/red]"
            table.add_row(p.display_name, cfg, avail, str(len(p.models)))

        console.print(table)

        # Database counts
        try:
            db = SessionLocal()
            conv_count = db.query(Conversation).count()
            msg_count = db.query(Message).count()
            db.close()
            console.print(f"[dim]Database: {settings.DATABASE_URL} | Total Conversations: {conv_count} | Total Messages: {msg_count}[/dim]")
        except Exception:
            pass

    async def load_file(self, filepath: str):
        clean_path = filepath.strip().strip('"').strip("'")
        if not os.path.exists(clean_path):
            console.print(f"[danger]File not found:[/danger] {clean_path}")
            return

        filename = os.path.basename(clean_path)
        is_image = filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"))

        with console.status(f"[bold cyan]Reading and analyzing {filename}...[/bold cyan]"):
            try:
                with open(clean_path, "rb") as f:
                    content_bytes = f.read()

                if is_image:
                    analysis_res = await image_service.analyze_image_multimodal(
                        image_bytes=content_bytes,
                        filename=filename,
                        user_prompt="Provide a comprehensive breakdown of the visual elements in this image."
                    )
                    props = analysis_res.get("properties", {})
                    analysis_text = analysis_res.get("analysis", "")
                    doc_snippet = (
                        f"--- Attached Image: {filename} ---\n"
                        f"Format: {props.get('format')} | Resolution: {props.get('width')}x{props.get('height')} | Aspect Ratio: {props.get('aspect_ratio')}\n"
                        f"Dominant Colors: {', '.join(props.get('dominant_hex_colors', []))}\n"
                        f"Visual Analysis:\n{analysis_text}\n"
                        f"--- End of Attached Image ---"
                    )
                    self.active_documents_text.append(doc_snippet)
                    console.print(f"[success]Successfully loaded and analyzed image:[/success] [bold]{filename}[/bold]")
                    console.print(f"[dim]Resolution: {props.get('width')}x{props.get('height')} | Palette: {', '.join(props.get('dominant_hex_colors', [])[:3])}. Attached to conversation context.[/dim]")
                    return

                # Ingest through DocumentService for non-image files
                db = SessionLocal()
                doc_record = document_service.process_uploaded_file(
                    db=db,
                    filename=filename,
                    file_bytes=content_bytes,
                    collection_name="cli-attachments"
                )
                db.close()

                # Get text preview
                text = document_service.extract_text(filename, content_bytes)
                self.active_documents_text.append(f"--- Document: {filename} ---\n{text[:4000]}\n--- End of Document ---")

                console.print(f"[success]Successfully loaded document:[/success] [bold]{filename}[/bold]")
                console.print(f"[dim]Extracted {doc_record.chunk_count} chunks ({doc_record.token_count} estimated tokens). Added to active context.[/dim]")
            except Exception as e:
                console.print(f"[danger]Failed to parse file:[/danger] {e}")

    async def generate_image_cmd(self, prompt_arg: str, style: str = "photorealistic", aspect_ratio: str = "1:1"):
        raw_prompt = prompt_arg.strip()
        if "--style" in raw_prompt:
            parts = raw_prompt.split("--style")
            raw_prompt = parts[0].strip()
            rest = parts[1].strip().split()
            if rest:
                style = rest[0].lower()
        if "--aspect" in raw_prompt:
            parts = raw_prompt.split("--aspect")
            raw_prompt = parts[0].strip()
            rest = parts[1].strip().split()
            if rest:
                aspect_ratio = rest[0]

        with console.status(f"[bold cyan]Rendering artwork via FLUX.1 neural engine...[/bold cyan]"):
            try:
                res = await image_service.generate_image(
                    prompt=raw_prompt,
                    style=style,
                    aspect_ratio=aspect_ratio
                )
            except Exception as e:
                console.print(f"[danger]Image generation failed:[/danger] {e}")
                return

        url = res.get("url", "")
        local_path = res.get("local_path", "")
        provider = res.get("provider", "flux.1")
        w = res.get("width", 1024)
        h = res.get("height", 1024)

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_row("[bold cyan]Prompt:[/bold cyan]", f"[white]{raw_prompt}[/white]")
        table.add_row("[bold cyan]Style:[/bold cyan]", f"[magenta]{style}[/magenta]")
        table.add_row("[bold cyan]Resolution:[/bold cyan]", f"[yellow]{w}x{h} ({aspect_ratio})[/yellow]")
        table.add_row("[bold cyan]Engine:[/bold cyan]", f"[green]{provider.upper()}[/green] [dim](Zero-Key FLUX.1 Neural)[/dim]")
        table.add_row("[bold cyan]Local File:[/bold cyan]", f"[bold underline blue]{local_path}[/bold underline blue]")
        table.add_row("[bold cyan]Web URL:[/bold cyan]", f"[dim]{url}[/dim]")

        console.print(Panel(
            table,
            title="[bold green]✦ Artwork Generated Successfully[/bold green]",
            border_style="green"
        ))

        md_content = f"![{raw_prompt}]({url})\n\n**Generated Artwork** (`{provider}`)\n- Prompt: *{raw_prompt}*\n- Style: `{style}` | Resolution: `{w}x{h}`\n- Saved to: `{local_path}`"
        self.messages.append({"role": "assistant", "content": md_content})
        self._save_message_to_db("assistant", md_content, model_used=f"image-{provider}")

    async def analyze_image_cmd(self, file_path_arg: str, query: str = "Describe this image in detail and analyze its composition."):
        clean_path = file_path_arg.strip().strip('"').strip("'")
        if not os.path.exists(clean_path):
            console.print(f"[danger]Image file not found:[/danger] {clean_path}")
            return

        with console.status(f"[bold cyan]Analyzing visual properties & scene decomposition...[/bold cyan]"):
            try:
                with open(clean_path, "rb") as f:
                    img_bytes = f.read()
                filename = os.path.basename(clean_path)
                result = await image_service.analyze_image_multimodal(
                    image_bytes=img_bytes,
                    filename=filename,
                    user_prompt=query
                )
            except Exception as e:
                console.print(f"[danger]Image analysis failed:[/danger] {e}")
                return

        props = result.get("properties", {})
        analysis_text = result.get("analysis", "")
        engine = result.get("engine", "visual_engine")

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_row("[bold cyan]Image:[/bold cyan]", f"[bold]{clean_path}[/bold]")
        table.add_row("[bold cyan]Format:[/bold cyan]", f"[magenta]{props.get('format', 'UNKNOWN')} ({props.get('color_mode', '')})[/magenta]")
        table.add_row("[bold cyan]Resolution:[/bold cyan]", f"[yellow]{props.get('width', 0)}x{props.get('height', 0)} ({props.get('aspect_ratio', '')})[/yellow]")
        table.add_row("[bold cyan]Megapixels:[/bold cyan]", f"[white]{props.get('megapixels', 0)} MP[/white]")
        table.add_row("[bold cyan]Brightness:[/bold cyan]", f"[white]{int(props.get('brightness', 0.5) * 100)}%[/white]")

        colors = props.get("dominant_colors", [])
        if colors:
            color_str = "  ".join([f"[{c}]■[/{c}] {c}" for c in colors])
            table.add_row("[bold cyan]Palette:[/bold cyan]", color_str)

        table.add_row("[bold cyan]Vision Engine:[/bold cyan]", f"[green]{engine}[/green]")

        console.print(Panel(
            table,
            title="[bold cyan]✦ Visual Property Inspection[/bold cyan]",
            border_style="cyan"
        ))

        console.print(Panel(
            Markdown(analysis_text),
            title="[bold magenta]Scene & Semantic Breakdown[/bold magenta]",
            border_style="magenta"
        ))

        self.messages.append({"role": "user", "content": f"/analyze {clean_path}"})
        self.messages.append({"role": "assistant", "content": f"### Image Analysis for `{clean_path}`\n\n{analysis_text}"})
        self._save_message_to_db("assistant", analysis_text, model_used="vision-engine")

    async def execute_search(self, query: str):
        with console.status(f"[bold cyan]Searching web for: {query}...[/bold cyan]"):
            results = await search_service.search(query, max_results=5)

        if not results:
            console.print("[yellow]No live web search results found for this query.[/yellow]")
            return

        table = Table(title=f"Web Search Results: {query}", border_style="cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="bold cyan")
        table.add_column("URL / Snippet", style="white")

        for idx, r in enumerate(results, 1):
            title = r.get("title", f"Result {idx}")
            url = r.get("url", "#")
            snippet = r.get("snippet", "").strip()
            cell = f"[blue underline]{url}[/blue underline]\n[dim]{snippet}[/dim]"
            table.add_row(str(idx), title, cell)

        console.print(table)

    async def execute_deep_research(self, topic: str):
        console.print(Panel(f"[bold]Initiating Autonomous Deep Research[/bold]\nTopic: [cyan]{topic}[/cyan]", border_style="cyan"))

        full_report = ""
        citations = []

        with console.status("[bold cyan]Executing multi-step research synthesis...[/bold cyan]") as status:
            async for chunk in research_service.run_deep_research_stream(topic):
                t = chunk.get("type")
                d = chunk.get("data", {})
                if t == "status":
                    status.update(f"[bold cyan]{d.get('status', '')}[/bold cyan]")
                elif t == "citation":
                    citations.append(d)
                elif t == "token":
                    full_report += d.get("token", "")

        console.print(Rule(style="cyan"))
        console.print(Markdown(full_report))
        console.print(Rule(style="cyan"))

        if citations:
            console.print("[bold cyan]References & Sources:[/bold cyan]")
            for idx, c in enumerate(citations[:5], 1):
                console.print(f"  [dim]{idx}.[/dim] [bold]{c.get('title')}[/bold] - [blue underline]{c.get('url')}[/blue underline]")
            console.print()

        # Save to session
        self.messages.append({"role": "user", "content": f"/research {topic}"})
        self.messages.append({"role": "assistant", "content": full_report})
        self._save_message_to_db("user", f"/research {topic}")
        self._save_message_to_db("assistant", full_report)

    async def execute_tool(self, arg_str: str):
        parts = arg_str.split(maxsplit=1)
        tool_name = parts[0]
        tool_input = parts[1] if len(parts) > 1 else ""

        if tool_name == "calculator":
            res = await tool_registry.execute_tool("calculator", {"expression": tool_input})
            console.print(f"[bold cyan]Calculator Output:[/bold cyan] [green]{res.get('result', res.get('error'))}[/green]")
        elif tool_name in ["datetime", "datetime_util"]:
            res = await tool_registry.execute_tool("datetime_util", {})
            console.print(f"[bold cyan]Current Datetime:[/bold cyan] [green]{res.get('formatted', res.get('utc_now'))}[/green]")
        else:
            res = await tool_registry.execute_tool(tool_name, {"query": tool_input} if "search" in tool_name else {"expression": tool_input})
            console.print(f"[bold cyan]Tool Output:[/bold cyan] {res}")

    async def handle_memory(self, arg: str):
        parts = arg.split(maxsplit=1)
        subcmd = parts[0].lower() if parts else "list"
        content = parts[1] if len(parts) > 1 else ""

        db = SessionLocal()
        try:
            if subcmd == "list":
                mems = memory_service.list_memories(db)
                if not mems:
                    console.print("[dim]No saved memories found.[/dim]")
                else:
                    table = Table(title="User Memories & Preferences", border_style="cyan")
                    table.add_column("Category", style="cyan")
                    table.add_column("Memory Fact", style="white")
                    table.add_column("Confidence", style="yellow")
                    for m in mems:
                        table.add_row(m.category, m.content, f"{m.confidence:.1f}")
                    console.print(table)
            elif subcmd == "add":
                if not content:
                    console.print("[danger]Usage: /memory add <preference or fact>[/danger]")
                else:
                    mem = memory_service.create_memory(db, content=content, category="user_preference")
                    console.print(f"[success]Saved memory preference:[/success] [bold]{mem.content}[/bold]")
            elif subcmd == "clear":
                # Clear memories
                mems = memory_service.list_memories(db)
                for m in mems:
                    memory_service.delete_memory(db, m.id)
                console.print("[success]All memories cleared.[/success]")
            else:
                console.print("[danger]Usage: /memory [list | add <fact> | clear][/danger]")
        finally:
            db.close()

    def show_history(self):
        if not self.messages:
            console.print("[dim]No conversation history in current session.[/dim]")
            return

        console.print(Rule(title="Session History", style="cyan"))
        for msg in self.messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                console.print(f"[bold cyan]You ❯[/bold cyan] {content}")
            else:
                console.print(f"[bold magenta]AetherAI ({self.model}) ❯[/bold magenta]")
                console.print(Markdown(content))
            console.print()
        console.print(Rule(style="cyan"))

    def save_conversation(self, path: Optional[str] = None):
        if not path:
            path = f"aether_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# AetherAI Conversation Log\n")
                f.write(f"- **Session ID**: `{self.conversation_id}`\n")
                f.write(f"- **Date**: {datetime.now(timezone.utc).isoformat()}\n")
                f.write(f"- **Model**: `{self.model}`\n")
                f.write(f"- **Persona**: `{self.persona}`\n\n---\n\n")

                for msg in self.messages:
                    role = "User" if msg["role"] == "user" else "AetherAI"
                    f.write(f"### {role}\n\n{msg.get('content', '')}\n\n")

            console.print(f"[success]Conversation successfully saved to:[/success] [bold]{path}[/bold]")
        except Exception as e:
            console.print(f"[danger]Failed to save conversation:[/danger] {e}")

    async def generate_response(self, user_prompt: str):
        # Check for natural language image generation intent
        intent = image_service.detect_image_generation_intent(user_prompt)
        if intent:
            await self.generate_image_cmd(
                intent["prompt"],
                style=intent.get("style", "photorealistic"),
                aspect_ratio=intent.get("aspect_ratio", "1:1")
            )
            return

        # Prepare context
        self.messages.append({"role": "user", "content": user_prompt})
        self._save_message_to_db("user", user_prompt)

        # Incorporate active file context if any
        context_messages = []
        if self.active_documents_text:
            doc_context = "\n\n".join(self.active_documents_text)
            context_messages.append({
                "role": "system",
                "content": f"The following files have been attached by the user for context:\n{doc_context}"
            })

        # Append persona prompt
        system_prompt = PERSONA_PROMPTS.get(self.persona, PERSONA_PROMPTS["general"])
        context_messages.extend(self.messages)

        console.print()
        console.print(f"[bold magenta]AetherAI[/bold magenta] [dim]({self.model})[/dim] ❯")

        full_content = ""
        full_reasoning = ""
        in_thinking_mode = False
        printed_thinking_header = False

        try:
            async for chunk in provider_registry.execute_stream_with_failover(
                messages=context_messages,
                model_id=self.model,
                system_prompt=system_prompt,
                temperature=0.7
            ):
                chunk_type = chunk.get("type")
                data = chunk.get("data", {})

                if chunk_type == "status":
                    status_text = data.get("status", "")
                    # Subtle status hint
                    console.print(f"[dim info]• {status_text}[/dim info]")

                elif chunk_type == "token":
                    token = data.get("token", "")
                    if not token:
                        continue

                    # Detect thinking delimiters
                    if "<think>" in token:
                        in_thinking_mode = True
                        token = token.replace("<think>", "")
                        if not printed_thinking_header:
                            console.print("[dim cyan]💭 Reasoning Process:[/dim cyan]")
                            printed_thinking_header = True

                    if "</think>" in token:
                        in_thinking_mode = False
                        token = token.replace("</think>", "")
                        console.print("\n[dim cyan]────────────────────────[/dim cyan]\n")

                    if in_thinking_mode:
                        full_reasoning += token
                        console.print(f"[dim italic cyan]{token}[/dim italic cyan]", end="", highlight=False)
                    else:
                        full_content += token
                        console.print(token, end="", highlight=False)

                elif chunk_type == "done":
                    break

                elif chunk_type == "error":
                    error_msg = data.get("error", "Unknown generation error")
                    console.print(f"\n[danger]Error:[/danger] {error_msg}")
                    return

            console.print("\n")
            
            # Save assistant response
            combined_saved = full_content
            if full_reasoning:
                combined_saved = f"<think>\n{full_reasoning}\n</think>\n\n{full_content}"
            self.messages.append({"role": "assistant", "content": combined_saved})
            self._save_message_to_db("assistant", combined_saved)

        except Exception as e:
            console.print(f"\n[danger]Generation error:[/danger] {str(e)}")

    async def run_interactive(self):
        self.print_banner()

        while True:
            try:
                prompt_text = f"aetherai ({self.model.split('/')[-1]}) ❯ "
                user_input = await asyncio.to_thread(
                    self._get_input,
                    prompt_text
                )

                cleaned = user_input.strip()
                if not cleaned:
                    continue

                if cleaned.startswith("/"):
                    should_continue = await self.handle_slash_command(cleaned)
                    if not should_continue:
                        break
                    continue

                await self.generate_response(cleaned)

            except KeyboardInterrupt:
                console.print("\n[dim]Action cancelled. (Press Ctrl+D or type /exit to quit)[/dim]")
                continue
            except EOFError:
                console.print("\n[dim cyan]Session ended. Goodbye![/dim cyan]")
                break
            except Exception as e:
                console.print(f"[danger]Unexpected CLI error:[/danger] {e}")


async def async_main():
    parser = argparse.ArgumentParser(description="AetherAI CLI - Intelligent Multi-Provider Terminal Workspace")
    parser.add_argument("prompt", nargs="*", help="Optional prompt for immediate one-shot response")
    parser.add_argument("-m", "--model", default=None, help="Language model to use (default: gemini-2.5-flash)")
    parser.add_argument("-p", "--persona", default="general", choices=list(PERSONA_PROMPTS.keys()), help="Persona role")
    parser.add_argument("-f", "--file", help="Path to document/code file to ingest as context")
    parser.add_argument("-s", "--search", help="Perform live web search on query")
    parser.add_argument("-r", "--research", help="Perform deep multi-round research on topic")
    parser.add_argument("-i", "--image", help="Generate artwork from prompt using FLUX.1 neural engine")
    parser.add_argument("-a", "--analyze", help="Analyze visual properties, colors and scene in image file")
    parser.add_argument("--style", default="photorealistic", help="Artwork style modifier (photorealistic, anime, cyberpunk, 3d_render, oil_painting)")
    parser.add_argument("--aspect", default="1:1", help="Image aspect ratio (1:1, 16:9, 9:16, 4:3)")
    parser.add_argument("--models", action="store_true", help="List available AI models and exit")
    parser.add_argument("--status", action="store_true", help="Display provider and system health and exit")

    args = parser.parse_args()
    cli = AetherCLI(model=args.model, persona=args.persona)

    # Check non-interactive quick flags
    if args.models:
        await cli.show_models()
        return

    if args.status:
        await cli.show_status()
        return

    if args.image:
        await cli.generate_image_cmd(args.image, style=args.style, aspect_ratio=args.aspect)
        return

    if args.analyze:
        await cli.analyze_image_cmd(args.analyze)
        return

    if args.search:
        await cli.execute_search(args.search)
        return

    if args.research:
        await cli.execute_deep_research(args.research)
        return

    # Check piped input from stdin if no command line prompt provided
    piped_stdin = ""
    if not args.prompt and not sys.stdin.isatty():
        try:
            piped_stdin = sys.stdin.read().strip()
        except Exception:
            pass

    if args.file:
        await cli.load_file(args.file)

    # If prompt passed via CLI arguments or piped stdin
    if args.prompt or piped_stdin:
        joined_prompt = " ".join(args.prompt).strip()
        if piped_stdin:
            if joined_prompt:
                final_prompt = f"```\n{piped_stdin}\n```\n\n{joined_prompt}"
            else:
                final_prompt = f"Analyze the following input:\n```\n{piped_stdin}\n```"
        else:
            final_prompt = joined_prompt

        await cli.generate_response(final_prompt)
        return

    # Enter full interactive REPL mode
    await cli.run_interactive()


def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
