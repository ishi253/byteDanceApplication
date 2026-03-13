# Meridian -- GTM Research Agent

A **Go-to-Market Research Agent** that produces structured market intelligence reports with citations and confidence scores. Built on **ByteDance DeerFlow** (open-source SuperAgent framework) with **Tavily** for web search and **DeepSeek** for reasoning. ModelArk-ready: swap to ModelArk endpoints with a single config change when available in your region.

**Live deployment**: Backend on [Cloud Run](https://console.cloud.google.com/run) (`deer-flow-backend`, `us-central1`, GCP project `bytedance-490020`) | Frontend on [Vercel](https://byte-dance-application.vercel.app)

## Status (what’s implemented)

- [x] **DeerFlow app running locally** (LangGraph + Gateway + Frontend)
- [x] **Local reverse proxy** on `http://localhost:2026` (nginx local-dev config writes logs/temp to repo-local paths)
- [x] **DeepSeek model configured** in `deer-flow/config.yaml` (OpenAI-compatible base URL)
- [x] **Web search configured** (Tavily enabled by default)
- [x] **GTM Research skill added** at `deer-flow/skills/public/gtm_research/SKILL.md`
- [x] **GTM-branded landing UX** (Hero copy, example topics, “How it works”, footer badge)
- [x] **Prototype RAG over uploads** (BM25 index + retrieval tools: `rag_ingest_uploads`, `rag_search`)
- [x] **Vector DB RAG ingestion (Milvus)** (tools: `rag_ingest_uploads_vector`, `rag_search_vector`; best-effort auto-ingest after upload)
- [x] **Cloud Run deployment** — backend on Cloud Run (`deer-flow-backend`, `us-central1`, GCP project `bytedance-490020`), frontend on Vercel (`byte-dance-application.vercel.app`)
- [x] **Fact-checking & data provenance** (`store_data_point`, `fact_check`, `get_sourced_data`) — automated contradiction detection, stale-data flagging, and coverage-gap analysis with per-data-point citation tracking
- [x] **Structured data extraction** (`extract_structured_data`, `list_uploaded_data_files`) — parse CSV/XLSX uploads into typed columns for agent analysis
- [x] **Mermaid diagram validation** (`validate_mermaid_syntax`) — syntax-check Mermaid diagrams before rendering
- [x] **UI-preserving summarization middleware** — compresses long conversations for the LLM while keeping full message history in the UI
- [x] **CI/CD pipeline** — backend unit tests + frontend CI on PRs, Cloud Run deploy on push to `prod`

## What It Does

- **GTM Research**: Enter a market or industry topic and get a structured report: market sizing (TAM/SAM/SOM), competitive landscape, customer segments, regulatory factors, trends, and strategic recommendations.
- **Data validation**: Cross-references statistics across sources and assigns confidence levels (High / Medium / Low).
- **Fact-checking**: Stores every data point with provenance (source URL, confidence, source type). Automated checks detect contradictions, stale data (2+ years old), single-source risks, numeric outliers, and coverage gaps across GTM sections. A dedicated fact-check reviewer subagent can verify entire reports.
- **Structured data extraction**: Upload CSV or XLSX files and the agent parses them into typed columns (numeric, percentage, currency, date, text) for quantitative analysis.
- **Diagram validation**: Mermaid diagrams in reports are syntax-checked before rendering, preventing broken visuals.
- **Uploads**: Add PDFs or industry reports in chat; the agent incorporates them into the analysis and cites them.
- **Powered by**: DeerFlow (agent orchestration, skills, sandbox), Tavily (web search), DeepSeek API (LLM). Architecture is designed to use ModelArk when available in your region.

## Architecture

```
User → [DeerFlow Web UI (Next.js)] ← Vercel (byte-dance-application.vercel.app)
            ↓
       [DeerFlow Agent (LangGraph)] ← Cloud Run (deer-flow-backend, us-central1)
            ├── GTM Research Skill (custom)
            ├── Web Search → Tavily
            ├── LLM Reasoning → DeepSeek API (ModelArk-featured model)
            ├── RAG / File access → Uploaded industry data
            ├── Fact-Checking → store_data_point, fact_check, get_sourced_data
            ├── Structured Data → extract_structured_data, list_uploaded_data_files
            ├── Diagram Validation → validate_mermaid_syntax
            ├── Fact-Check Reviewer (subagent)
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

Open **http://localhost:2026**. Use the landing example topics or type a GTM research question in the chat.

### ModelArk migration

The app uses the DeepSeek API directly because ModelArk is not available in the US. To switch to ModelArk when it is available, update `deer-flow/config.yaml` under `models`:

- Set `base_url` to your ModelArk endpoint.
- Set `api_key` to your ModelArk API key (e.g. `$MODELARK_API_KEY`).

No other code changes are required.

## Deployment

### Backend — Cloud Run

The backend runs as a single-container Cloud Run service (`deer-flow-backend`) in `us-central1` (GCP project `bytedance-490020`).

- **Dockerfile**: `deer-flow/docker/Dockerfile.cloudrun` — Python 3.12-slim, bundles Nginx + Gateway + LangGraph, exposes port 8080
- **Cloud Build**: `deer-flow/cloudbuild.yaml` — builds the Docker image and deploys to Cloud Run (2 CPU, 2 GB RAM, max 5 instances, 600s timeout)
- **Trigger**: Push to the `prod` branch (via `.github/workflows/deploy-backend-cloudrun.yml`)
- **Secrets**: `TAVILY_API_KEY`, `DEEPSEEK_API_KEY`, and `DEERFLOW_PG_DSN` are injected from GCP Secret Manager

### Frontend — Vercel

The Next.js frontend is deployed on Vercel at [`byte-dance-application.vercel.app`](https://byte-dance-application.vercel.app).

### Docker dev environment

`deer-flow/docker/docker-compose-dev.yaml` orchestrates all services locally (Nginx, Frontend, Gateway, LangGraph) with hot reload via volume mounts. The unified URL is `http://localhost:2026`.

## CI/CD

Three GitHub Actions workflows:

| Workflow | File | Trigger | What it does |
|----------|------|---------|-------------|
| Backend unit tests | `.github/workflows/backend-unit-tests.yml` | PRs | `ruff lint` + `pytest` (~277 tests) |
| Frontend CI | `.github/workflows/frontend-ci.yml` | PRs | `pnpm lint` + `pnpm typecheck` + `pnpm build` |
| Cloud Run deploy | `.github/workflows/deploy-backend-cloudrun.yml` | Push to `prod` | `gcloud builds submit` → Cloud Run |

## Project layout

- **`deer-flow/`** — DeerFlow clone with GTM customizations.
  - **`skills/public/gtm_research/SKILL.md`** — GTM Research skill (report structure, validation rules, workflow).
  - **`config.yaml`** — Models (DeepSeek), tools (web search, fact-check, structured data, mermaid), skills path.
  - **`frontend/`** — Next.js UI: Meridian/GTM branding, example topics, “How it works” section, footer badge.
  - **`backend/src/community/fact_check/`** — `store_data_point`, `fact_check`, `get_sourced_data` tools for data provenance and automated validation.
  - **`backend/src/community/structured_data/`** — `extract_structured_data`, `list_uploaded_data_files` tools for CSV/XLSX parsing.
  - **`backend/src/community/mermaid_validate/`** — `validate_mermaid_syntax` tool for diagram syntax checking.
  - **`backend/src/subagents/builtins/fact_check_reviewer.py`** — Fact-check reviewer subagent that verifies report accuracy via web search and cross-referencing.
  - **`backend/src/agents/middlewares/ui_preserving_summarization_middleware.py`** — Summarizes long conversations for the LLM while preserving full message history in the UI.
  - **`docker/Dockerfile.cloudrun`** — Production Dockerfile for Cloud Run.
  - **`docker/docker-compose-dev.yaml`** — Docker Compose for local development.
  - **`cloudbuild.yaml`** — Google Cloud Build config for Cloud Run deploys.
  - **`.github/workflows/`** — CI/CD: `backend-unit-tests.yml`, `frontend-ci.yml`, `deploy-backend-cloudrun.yml`.

## License

DeerFlow is MIT. This project follows the same license for the customizations.
