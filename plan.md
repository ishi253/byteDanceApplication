## Phase 1 – Current State & Tracing — DONE

- **Confirm LangGraph + Gateway health**
  - Start stack with `cd deer-flow && make dev`.
  - Verify `http://localhost:2026` (frontend) and `http://localhost:2024` returns `{"ok": true}`.
  - Check `deer-flow/logs/langgraph.log` for startup errors.
- **Verify persistence + GCP Postgres**
  - Ensure `DEERFLOW_PG_DSN` in `.env` points to Cloud SQL Postgres.
  - Create a chat, restart `make dev`, confirm thread and messages persist.
- **Verify LangSmith tracing**
  - Ensure `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` are set in `.env`.
  - Run a few chats and confirm runs appear in the LangSmith `ByteDance` project.

## Phase 2 – Chat UX improvements — DONE

- **Fix "new chat" navigation**
  - Align `useThreadChat` hook so that:
    - `/workspace/chats/new` generates a new client-side UUID.
    - When the first message is sent, use the created `thread_id` returned by LangGraph to `router.replace` to `/workspace/chats/{id}`.
  - Ensure the initial message appears in the new thread immediately (optimistic UI from `useThreadStream`).
- **Polish input and layout**
  - Keep existing `InputBox` but ensure:
    - Submit-on-Enter behavior is smooth.
    - Streaming indicator and follow-up suggestions are unobtrusive.
  - Confirm responsiveness of the chat layout and artifacts panel.

## Phase 3 – Dual-history summarization (keep full UI history) — DONE

- **Design dual-history state**
  - Extend `ThreadState` to add a `summary_history` field (string or list of messages).
  - Decide on summary format: single markdown block that captures earlier turns.
- **Implement custom summarization middleware**
  - Create `UiPreservingSummarizationMiddleware` in `backend/src/agents/middlewares/`.
  - On trigger:
    - Read `summarization` config from `config.yaml` (token threshold, keep policy).
    - Summarize older messages into `summary_history`.
    - Do **not** mutate `messages` in the stored state.
  - In `before_model`:
    - Build model input as `summary_history + last N messages`.
    - Pass this to the LLM while leaving persisted `messages` untouched.
- **Wire middleware into lead agent**
  - Replace current `SummarizationMiddleware` integration in `lead_agent/agent.py` with the new middleware.
  - Reuse existing config structure so future tuning is just editing `config.yaml`.

## Phase 4 – Frontend integration with summaries — PARTIALLY DONE

- **Expose summary in thread values**
  - `summary_history` is part of `AgentThreadState.values` returned over the LangGraph API.
- **Optional: Visual marker for summarization** — TBD
  - In `MessageList`, if `summary_history` exists:
    - Insert a small "Earlier context summarized" system chip between older and newer messages.
    - Display a collapsible block with the summary text if the user expands it.
  - Keep the full raw messages rendered as today so UX does not regress.

## Phase 5 – Testing, observability, and docs — IN PROGRESS

- **Backend tests** — DONE
  - Add unit tests around the new middleware:
    - When token thresholds are exceeded, `summary_history` is populated.
    - `messages` continues to hold all prior turns.
    - Model input in LangSmith traces shows summary + recent messages only.
- **Manual QA** — DONE
  - Long, multi-turn chats to verify:
    - UI still shows full history.
    - Summaries appear only when conversations are long.
    - No regressions in uploads, RAG tools, or artifacts.
- **Documentation** — IN PROGRESS
  - Update root `README.md` with:
    - Note about GCP Postgres persistence.
    - Note about LangSmith tracing.
  - Update `deer-flow/backend/CLAUDE.md` with:
    - Description of the new UI-preserving summarization middleware.
    - How to tune or disable summarization via `config.yaml`.

## Phase 6 – GTM Custom Tools & Deployment — DONE

- **Fact-checking system**
  - `store_data_point` — store sourced research data with provenance (section, field, value, source, confidence, source type)
  - `fact_check` — automated validation: contradictions, stale data (2+ years), single-source risks, numeric outliers, coverage gaps
  - `get_sourced_data` — retrieve all data points grouped by section with full citation metadata
  - `fact_check_reviewer` subagent — dedicated reviewer that verifies reports via web search and cross-referencing
- **Structured data extraction**
  - `extract_structured_data` — parse CSV/XLSX uploads into typed columns (numeric, percentage, currency, date, text)
  - `list_uploaded_data_files` — list available data files for the current thread
- **Mermaid diagram validation**
  - `validate_mermaid_syntax` — syntax-check Mermaid diagrams before rendering (Node.js mermaid-cli or heuristic fallback)
- **Cloud Run + Vercel deployment**
  - Backend on Cloud Run (`deer-flow-backend`, `us-central1`, GCP project `bytedance-490020`)
  - Frontend on Vercel (`byte-dance-application.vercel.app`)
  - `Dockerfile.cloudrun` + `cloudbuild.yaml` for production builds
- **CI/CD pipeline**
  - `backend-unit-tests.yml` — ruff lint + pytest (~277 tests) on PRs
  - `frontend-ci.yml` — ESLint + TypeScript + build on PRs
  - `deploy-backend-cloudrun.yml` — Cloud Run deploy on push to `prod`
- **Meridian branding** — project renamed to "Meridian -- GTM Research Agent"
