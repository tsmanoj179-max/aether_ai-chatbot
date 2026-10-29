# AetherAI — Intelligent AI Workspace

<p align="center">
  <strong>A modern, production-oriented multi-provider AI assistant featuring real-time streaming, document intelligence (RAG), live web research, persistent long-term memory, and a controlled tool-execution architecture.</strong>
</p>

---

## 🌟 Key Capabilities

- **Zero-Barrier First-Run (Deterministic Mock Engine)**:
  Works instantly out-of-the-box with **zero API keys required**. Simulates realistic streaming, coding, research synthesis, and tool execution with clear simulation provenance tags.
- **Multi-Provider AI Architecture**:
  Native adapter integrations for:
  - **Google Gemini** (`gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-1.5-flash`) via official `google-genai` SDK.
  - **GroqCloud** (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`).
  - **OpenAI-Compatible Endpoints** (`gpt-4o`, `gpt-4o-mini`, vLLM, LocalAI, DeepSeek).
  - **Ollama Local Inference** (`ollama/llama3.2`, etc.) with zero GPU prerequisite.
  - **Deterministic Demonstration Simulator** (`aether-mock-omni`, `aether-mock-code`, `aether-mock-fast`).
- **Resilient Model Routing & Failover**:
  Transparent capability detection with bounded exponential backoff failover if temporary rate limits or provider outages occur.
- **Real-Time Streaming Protocol**:
  Native Server-Sent Events (SSE) with token streaming, live tool execution status pulses, source citation delivery, and clean client-side cancellation.
- **Document Intelligence (RAG)**:
  Parses **PDF, DOCX, TXT, Markdown, CSV, and XLSX**. Sliding-window chunking, sparse TF-IDF/BM25 vectorization, and cosine similarity ranking optimized for CPU execution.
- **Web Research & Bounded Exploration**:
  - *Standard Web Search*: Grounding via Tavily, Brave, or DuckDuckGo.
  - *Deep Research Studio*: 5-step bounded workflow: deconstruct query, formulate multi-angle searches, deduplicate sources, extract verified claims, identify evidence gaps, and compile structured reports.
- **Dual-Layer Memory & Personalization**:
  Separates conversational history from user-curated long-term preferences, facts, and instructions. Complete review, edit, toggle, and wipe controls.
- **Secure Tool Execution Lab**:
  Isolated AST mathematical expression evaluation (no unrestricted `eval`), UTC/local datetime utilities, dataset analysis summaries, and audit logging.
- **Crafted User Interface**:
  - Dark-mode-first aesthetic with dynamic light theme switching.
  - Responsive 3-pane layout: collapsible navigation sidebar, conversation workspace, and sliding contextual panel.
  - Command palette (`Ctrl+K` or `⌘K`), code block syntax highlighting with one-click copy, citation popovers, voice input (Web Speech API), and TTS read-aloud.

---

## 🏗️ Architecture & Project Structure

```
d:\AIChatBot\
├── .env.example                # Sample environment configuration
├── .gitignore                  # Git exclusion rules
├── README.md                   # Complete documentation
├── run_backend.ps1             # Backend startup script (PowerShell)
├── run_frontend.ps1            # Frontend startup script (PowerShell)
├── run_all.ps1                 # Unified full-stack launcher (PowerShell)
│
├── backend\
│   ├── app\
│   │   ├── main.py             # FastAPI entrypoint, CORS, lifespan, exception handler
│   │   ├── config.py           # Typed Pydantic Settings
│   │   ├── database.py         # SQLAlchemy engine, sessions, Base declarative
│   │   ├── models\             # Conversation, Message, Document, Memory, Audit
│   │   ├── schemas\            # Pydantic validation schemas
│   │   ├── providers\          # Mock, Gemini, Groq, OpenAI, Ollama adapters & registry
│   │   ├── services\           # Chat, RAG, Web Search, Deep Research, Memory, Tools
│   │   └── api\v1\             # REST & SSE endpoints (/health, /conversations, /chat, etc.)
│   ├── tests\                  # Automated Pytest suite
│   ├── requirements.txt        # Backend dependencies
│   └── uploads\                # Sandboxed storage for uploaded documents
│
└── frontend\
    ├── index.html              # HTML entrypoint
    ├── vite.config.ts          # Vite configuration with API proxy
    ├── tailwind.config.js      # Tailwind design system tokens
    ├── package.json            # Frontend dependencies
    └── src\
        ├── main.tsx            # React root mount
        ├── App.tsx             # Root layout & modal coordinator
        ├── index.css           # Design tokens, typography, sleek scrollbars
        ├── api\client.ts       # Typed REST client & SSE stream reader
        ├── store\useAppStore.ts# State management hook
        ├── types\index.ts      # TypeScript interfaces
        └── components\
            ├── layout\         # Header, Sidebar, ContextPanel
            ├── chat\           # ChatViewport, MessageItem, Composer, CodeBlock, Citations
            ├── settings\       # SettingsModal & Provider setup
            └── common\         # CommandPalette, Toast notifications
```

---

## 🚀 Quick Start (Windows PowerShell)

### Prerequisites
- **Python**: 3.10+ (Tested on Python 3.14.5)
- **Node.js**: v18+ (Tested on Node v25.2.1 / npm 11.6.2)
- Hardware: Standard CPU (e.g. Intel Core i7 with 16 GB RAM). No dedicated GPU required.

### 1. Installation

Open **Windows PowerShell** in `d:\AIChatBot`:

```powershell
# 1. Set up Python virtual environment and backend dependencies
python -m venv .venv
.\.venv\Scripts\pip.exe install -r backend\requirements.txt

# 2. Set up Frontend dependencies
Set-Location frontend
cmd /c "npm install"
Set-Location ..
```

### 2. Launching the Application

#### Option A: Universal Application Launcher (Single-Click, Hidden Terminals & Auto-Close)
Double-click either launcher in the project root:
- **`AetherAI.bat`** or **`AetherAI.vbs`** (completely silent startup with zero black terminal windows)
  - Starts FastAPI backend and Vite frontend completely hidden in the background.
  - Automatically opens AetherAI in a native desktop application window.
  - **Auto-Shutdown**: When you close the chatbot window (clicking the `X` button), close the browser tab, or click the in-app Exit button, all backend and frontend services terminate automatically, freeing ports 8000 and 5173.

#### Option B: Developer Mode (Visible Console Windows)
For debugging and viewing real-time server logs in dedicated terminals:
- `.\run_all.bat` (opens backend and frontend in separate CMD windows)
- Or individually: `.\run_backend.bat` and `.\run_frontend.bat`
- Clean emergency stop: `.\stop_aether.bat` (instantly terminates all services and frees ports)

#### Option B: PowerShell with Policy Bypass
If PowerShell script execution is restricted on your system, use `-ExecutionPolicy Bypass`:
```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1
```
Or run the scripts individually:
```powershell
powershell -ExecutionPolicy Bypass -File .\run_backend.ps1
powershell -ExecutionPolicy Bypass -File .\run_frontend.ps1
```
Or enable script execution for your current PowerShell session only:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_all.ps1
```

Now open **http://127.0.0.1:5173** in your browser. The application will start immediately with all models configured and ready.

---

## 💻 AetherAI CLI Mode (Interactive Terminal Workspace)

Just like the **Antigravity CLI (`agy`)**, AetherAI features a full-fledged, interactive, terminal-based AI assistant with rich formatting, multi-turn history, slash commands, live streaming, and document/research integration.

### Starting CLI Mode

```cmd
.\run_cli.bat
```
*Or via Python directly:*
```bash
python aether.py
```

### CLI Features & Capabilities

- **Interactive REPL Session**: Persistent multi-turn conversations with history recall (Up/Down arrow keys) and command auto-completion (`~/.aetherai_history`).
- **Real-Time Token Streaming**: Watch responses stream directly in the terminal, including dedicated collapsible reasoning blocks (`<think>...</think>`).
- **Unified Database Synchronization**: Any conversation you have in the CLI is automatically synchronized to SQLite (`aetherai.db`), allowing you to view and continue it in the Web UI!
- **Zero-Key Ready**: All 16 models work out-of-the-box in the terminal without requiring private API keys.

### Slash Commands in REPL

| Command | Action | Example |
| :--- | :--- | :--- |
| `/help` | Display interactive command cheatsheet | `/help` |
| `/models` | View all 16 available models, context windows & tiers | `/models` |
| `/model <id>` | Switch the active language model on the fly | `/model gpt-4o` |
| `/persona <role>` | Switch persona (`general`, `coder`, `researcher`, `analyst`, `writer`) | `/persona coder` |
| `/search <query>` | Run live web search with citations and URLs | `/search latest NASA news` |
| `/research <topic>` | Execute autonomous 5-step deep research report | `/research quantum computing 2026` |
| `/file <path>` | Ingest and chunk local files (PDF, DOCX, TXT, code, CSV) into context | `/file src/main.py` |
| `/tool <name> [args]` | Execute AST math calculator or datetime utilities | `/tool calculator 17 * 19` |
| `/memory [list\|add\|clear]` | Review or record user personalization facts | `/memory add User prefers TypeScript` |
| `/history` | Print previous turns in current conversation | `/history` |
| `/save [path]` | Export conversation as a Markdown file | `/save session_notes.md` |
| `/status` | View system health, database counts, and provider states | `/status` |
| `/clear` or `/new` | Reset context and start a new conversation session | `/new` |
| `/exit` or `/quit` | Save and exit the terminal REPL | `/exit` |

### One-Shot & Pipeline Mode (Unix Philosophy)

Run quick queries without entering the interactive shell:
```bash
# Direct prompt
python aether.py "Explain the Raft consensus algorithm with Python diagrams"

# Specify model and persona
python aether.py -m gpt-4o -p coder "Write an async worker pool in Python"

# Web search directly from terminal
python aether.py --search "James Webb space telescope discoveries"

# Deep multi-step research synthesis
python aether.py --research "Solid state battery breakthroughs 2026"

# Piped stdin analysis (piping code/logs directly to AI)
type server.log | python aether.py "Diagnose the error in this log"
```

---

## 🔑 Configuring Real AI Providers (Optional)

To enable live cloud or local inference, copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

### 1. Google Gemini API (Recommended for Free Tier & Vision)
1. Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Set in `.env`:
   ```ini
   GEMINI_API_KEY=your_gemini_api_key_here
   DEFAULT_PROVIDER=gemini
   DEFAULT_MODEL=gemini-2.5-flash
   ```

### 2. GroqCloud API (Recommended for Ultra-Fast LPU Inference)
1. Get a free API key at [Groq Console](https://console.groq.com/keys).
2. Set in `.env`:
   ```ini
   GROQ_API_KEY=your_groq_api_key_here
   ```

### 3. OpenAI / OpenAI-Compatible (LocalAI, vLLM, DeepSeek)
1. Set in `.env`:
   ```ini
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_API_BASE=https://api.openai.com/v1
   ```

### 4. Ollama (Local CPU Inference)
1. Install [Ollama](https://ollama.com/) and run `ollama run llama3.2`.
2. AetherAI connects automatically to `http://localhost:11434`.

### 5. Web Search Providers (Tavily / Brave)
1. Set in `.env`:
   ```ini
   TAVILY_API_KEY=your_tavily_api_key
   # or
   BRAVE_API_KEY=your_brave_api_key
   ```
   *(If omitted, AetherAI uses DuckDuckGo with verified link extraction).*

---

## 🧪 Testing & Verification

### Running Backend Pytest Suite
```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -v
```
**Results Verified**:
- `test_root_endpoint`: PASSED
- `test_health_endpoint`: PASSED
- `test_providers_and_models`: PASSED
- `test_mock_provider_generation`: PASSED
- `test_mock_provider_streaming`: PASSED
- `test_conversation_crud_and_persistence`: PASSED
- `test_document_chunking_and_similarity`: PASSED
- `test_calculator_tool`: PASSED (Including division-by-zero & AST security checks)
- `test_datetime_tool`: PASSED
- `test_memories_crud`: PASSED

### Running Frontend Production Build
```powershell
cmd /c "cd frontend && npm run build"
```
**Results Verified**:
- Type checking: PASSED
- Vite production bundle generated in `frontend/dist/` in 1.29s.

---

## 🛡️ Security & Privacy Guardrails

1. **Localhost Binding**: Development server binds strictly to `127.0.0.1` by default to prevent unauthorized network exposure.
2. **Zero Client Secret Storage**: API keys reside exclusively in server-side `.env` files and are never passed to the frontend or localStorage.
3. **AST-Isolated Calculator**: Math evaluation parses Python AST nodes with strict operator whitelisting; arbitrary code execution (`eval`/`exec`) is forbidden.
4. **Sandboxed File Ingestion**: File uploads enforce strict MIME type checks, extension whitelisting, randomized disk filenames, and a 25MB file-size ceiling.
5. **Path Traversal Shield**: All file access endpoints enforce normalized path constraints.

---

## 📋 Implemented Features Summary

| Component | Status | Highlights |
| :--- | :---: | :--- |
| **Deterministic Mock Engine** | ✅ Complete | Zero-key demonstration mode, streaming simulation, distinct provenance tagging |
| **Multi-Provider Architecture** | ✅ Complete | Google Gemini, GroqCloud, OpenAI-compatible, Ollama, and Mock adapters |
| **Failover & Retry Engine** | ✅ Complete | Bounded retry with graceful failover to simulator or secondary provider |
| **SSE Streaming** | ✅ Complete | Token-by-token streaming, tool status pulses, source citations, client cancellation |
| **Document Intelligence (RAG)** | ✅ Complete | Multi-format extraction (PDF, DOCX, TXT, CSV), token chunking, cosine vector similarity |
| **Web Research** | ✅ Complete | Standard web grounding + 5-step bounded Deep Research workflow |
| **Long-Term Memory** | ✅ Complete | User-governed preference curation, prompt injection, editing, and deletion |
| **Tool Registry & Audit** | ✅ Complete | AST calculator, datetime utility, CSV data analyst, execution audit logging |
| **Premium Interface** | ✅ Complete | 3-pane layout, dark/light themes, Lucide icons, command palette (`Ctrl+K`), voice input/TTS |
| **Automated Verification** | ✅ Complete | 100% passing backend tests and production frontend bundle |

---

## 🔮 Recommended Next Improvements

1. **Hybrid Vector Search**: Complement sparse TF-IDF with an optional dense embedding model (e.g., `all-MiniLM-L6-v2` via `fastembed` or SQLite `sqlite-vec`).
2. **Multi-User Authentication**: Introduce JWT authentication and row-level tenant isolation for enterprise team deployments.
3. **Sandboxed Code Execution**: Containerized Docker execution environment with network isolation for running arbitrary generated scripts.
