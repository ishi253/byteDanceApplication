# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A **Go-to-Market Research Agent** built on ByteDance's **DeerFlow** (open-source SuperAgent/LangGraph framework). The agent produces structured market intelligence reports (TAM/SAM/SOM, competitive analysis, confidence scores) using Tavily for web search and DeepSeek for LLM reasoning. ModelArk-ready: one config change in `deer-flow/config.yaml` swaps to ModelArk endpoints.

All application code lives inside `deer-flow/`. The root contains `README.md`, `plan.md`, and this file.

## Setup & Commands

**Working directory for all commands**: `deer-flow/`

```bash
# First-time setup
make check       # Verify prerequisites (Node.js 22+, Python 3.12+, uv, pnpm, nginx)
make config      # Generate config.yaml and .env from templates (aborts if files already exist)
make install     # Install frontend (pnpm) + backend (uv) dependencies

# Development
make dev         # Start all services: LangGraph (:2024) + Gateway (:8001) + Frontend (:3000) + nginx (:2026)
make dev-daemon  # Same, in background
make stop        # Stop all services (run twice if sessions get stuck)
make clean       # Kill processes + remove temp files

# Backend (from deer-flow/backend/)
make lint        # ruff lint
make format      # ruff format
make test        # Run all unit tests (~277 tests)

# Frontend (from deer-flow/frontend/)
pnpm lint        # ESLint
pnpm typecheck   # tsc --noEmit
pnpm build       # Production build
```

**Required env vars** in `deer-flow/.env`:
```
DEEPSEEK_API_KEY=...   # https://platform.deepseek.com
TAVILY_API_KEY=...
```

The unified dev URL is `http://localhost:2026` (nginx proxy). Individual services: LangGraph `:2024`, Gateway `:8001`, Frontend `:3000`.

## Architecture

### Backend (`deer-flow/backend/src/`)

The core agent is built on **LangGraph** with a **middleware chain** wrapping tool execution:

```
ThreadData → Uploads → Sandbox → DanglingToolCall → Summarization
  → TodoList → Title → Memory → ViewImage → SubagentLimit → Clarification
```

**Key directories:**
- `agents/lead_agent/` — Main agent factory; assembles tools via `get_available_tools()` (config tools + MCP tools + built-ins)
- `agents/middlewares/` — 11 ordered middleware components (see chain above)
- `agents/memory/` — Per-thread LLM-extracted fact storage with 30s debounced writes
- `gateway/` — FastAPI REST API with 6 routers (models, skills, memory, uploads, artifacts, MCP)
- `sandbox/` — Abstract `Sandbox` interface with `LocalSandboxProvider` and Docker-based `AioSandboxProvider`; virtual paths `/mnt/user-data/` ↔ `backend/.deer-flow/threads/{id}/user-data/`
- `community/` — Plugin tools: `tavily/`, `jina_ai/`, `firecrawl/`, `rag_bm25/`, `rag_milvus/`
- `subagents/` — Background thread pool (3 workers, 15-min timeout) for task delegation
- `mcp/` — Model Context Protocol server integration
- `reflection/` — Dynamic class/variable resolution (`resolve_variable`, `resolve_class`) used throughout config

**Python package manager**: `uv`. Dependencies in `pyproject.toml` (Python ≥3.12).

### Frontend (`deer-flow/frontend/src/`)

**Next.js 16** App Router with **React 19**, TypeScript, Tailwind CSS 4, Shadcn UI.

- `app/` — Two routes: `/` (landing) and `/workspace/chats/[thread_id]` (chat UI)
- `core/` — Business logic: `threads/` (hooks: `useThreadStream`, `useSubmitThread`, `useThreads`), `api/` (LangGraph SDK singleton), `artifacts/`, `memory/`, `skills/`, `mcp/`
- `components/workspace/` — Chat messages, artifacts panel, settings
- State: TanStack Query (server state) + localStorage (user preferences)

**Package manager**: `pnpm 10.26.2`.

### Configuration System

Two config files (both in `deer-flow/`):

1. **`config.yaml`** — Models, tools, tool groups, sandbox provider, skills paths, memory, channel configs. Values starting with `$` are resolved as env vars at runtime.
2. **`extensions_config.json`** — MCP server definitions and skills enabled/disabled flags.

Config resolution order: explicit arg → `DEER_FLOW_CONFIG_PATH` env var → current dir → parent dir.

### GTM Customizations

- **Skill**: `deer-flow/skills/public/gtm_research/SKILL.md` — triggers on GTM/market research queries; defines report structure (TAM/SAM/SOM, competitive landscape, confidence scoring, citation tracking)
- **Frontend**: GTM branding in landing page hero, example topics, "How it works" section, footer badge
- **RAG**: BM25 tools (`rag_ingest_uploads`, `rag_search`) and Milvus vector tools (`rag_ingest_uploads_vector`, `rag_search_vector`) for uploaded PDF analysis

### ModelArk Migration

To switch from DeepSeek API to ModelArk: update `deer-flow/config.yaml` under `models` — change `base_url` to ModelArk endpoint and `api_key` to `$MODELARK_API_KEY`. No code changes needed.

## CI

GitHub Actions (`.github/workflows/backend-unit-tests.yml`) runs `uv sync --group dev && make lint && make test` in `backend/` on PRs. Backend tests must pass before merging.
