# GTM Research Agent

A **Go-to-Market Research Agent** that produces structured market intelligence reports with citations and confidence scores. Built on **ByteDance DeerFlow** (open-source SuperAgent framework) with **Tavily** for web search and **DeepSeek** for reasoning. ModelArk-ready: swap to ModelArk endpoints with a single config change when available in your region.

## Status (what’s implemented)

- [x] **DeerFlow app running locally** (LangGraph + Gateway + Frontend)
- [x] **Local reverse proxy** on `http://localhost:2026` (nginx local-dev config writes logs/temp to repo-local paths)
- [x] **DeepSeek model configured** in `deer-flow/config.yaml` (OpenAI-compatible base URL)
- [x] **Web search configured** (Tavily enabled by default)
- [x] **GTM Research skill added** at `deer-flow/skills/public/gtm_research/SKILL.md`
- [x] **GTM-branded landing UX** (Hero copy, example topics, “How it works”, footer badge)
- [x] **Prototype RAG over uploads** (BM25 index + retrieval tools: `rag_ingest_uploads`, `rag_search`)
- [x] **Vector DB RAG ingestion (Milvus)** (tools: `rag_ingest_uploads_vector`, `rag_search_vector`; best-effort auto-ingest after upload)
- [ ] **Cloud Run deployment** + live demo URL — Dockerfiles production-ready; run Phase 3–6 of `plan.md` to deploy

## What It Does

- **GTM Research**: Enter a market or industry topic and get a structured report: market sizing (TAM/SAM/SOM), competitive landscape, customer segments, regulatory factors, trends, and strategic recommendations.
- **Data validation**: Cross-references statistics across sources and assigns confidence levels (High / Medium / Low).
- **Uploads**: Add PDFs or industry reports in chat; the agent incorporates them into the analysis and cites them.
- **Powered by**: DeerFlow (agent orchestration, skills, sandbox), Tavily (web search), DeepSeek API (LLM). Architecture is designed to use ModelArk when available in your region.

## Architecture

```
User → [DeerFlow Web UI (Next.js)]
            ↓
       [DeerFlow Agent (LangGraph)]
            ├── GTM Research Skill (custom)
            ├── Web Search → Tavily
            ├── LLM Reasoning → DeepSeek API (ModelArk-featured model)
            ├── RAG / File access → Uploaded industry data
            └── Report Generation → Structured Markdown with confidence scores
```

## ByteDance usage

| Component    | Role |
|------------|------|
| **DeerFlow** | ByteDance open-source SuperAgent framework — core orchestration, skills, sandbox, UI. |
| **DeepSeek** | Models featured on ModelArk; used via DeepSeek API directly because ModelArk is not available in the US. One config change swaps to ModelArk when region is supported. |
| **Milvus / RAG** | DeerFlow supports Milvus for RAG; this project can use file uploads + agent file reading for industry data. |

## Setup

### Prerequisites

- **Python 3.12+**
- **Node.js 22+**
- **uv** (Python): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **pnpm** (optional): `npm install -g pnpm` (if not installed, `make install` / `make dev` will fall back to npm for the frontend)

### 1. Enter the DeerFlow directory

```bash
cd deer-flow
```

### 2. Generate config (if not already done)

```bash
make config
```

This creates `config.yaml` and `.env` from templates.

### 3. Configure environment

Edit **`.env`** in `deer-flow/`:

```bash
# Required for LLM
DEEPSEEK_API_KEY=your-deepseek-api-key   # https://platform.deepseek.com

# Required for web search (use one)
TAVILY_API_KEY=your-tavily-api-key
```

### 4. Install and run

```bash
make install
make dev
```

Open **http://localhost:3000**. Use the landing example topics or type a GTM research question in the chat.

### ModelArk migration

The app uses the DeepSeek API directly because ModelArk is not available in the US. To switch to ModelArk when it is available, update `deer-flow/config.yaml` under `models`:

- Set `base_url` to your ModelArk endpoint.
- Set `api_key` to your ModelArk API key (e.g. `$MODELARK_API_KEY`).

No other code changes are required.

## Project layout

- **`deer-flow/`** — DeerFlow clone with GTM customizations.
  - **`deer-flow/skills/public/gtm_research/SKILL.md`** — GTM Research skill (report structure, validation rules, workflow).
  - **`deer-flow/config.yaml`** — Models (DeepSeek), tools (web search), skills path.
  - **`deer-flow/frontend/`** — Next.js UI: GTM branding, example topics, “How it works” section, footer badge.

## License

DeerFlow is MIT. This project follows the same license for the customizations.
