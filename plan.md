## Phase 1 – Current State & Tracing

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

## Phase 2 – Chat UX improvements

- **Fix “new chat” navigation**
  - Align `useThreadChat` hook so that:
    - `/workspace/chats/new` generates a new client-side UUID.
    - When the first message is sent, use the created `thread_id` returned by LangGraph to `router.replace` to `/workspace/chats/{id}`.
  - Ensure the initial message appears in the new thread immediately (optimistic UI from `useThreadStream`).
- **Polish input and layout**
  - Keep existing `InputBox` but ensure:
    - Submit-on-Enter behavior is smooth.
    - Streaming indicator and follow-up suggestions are unobtrusive.
  - Confirm responsiveness of the chat layout and artifacts panel.

## Phase 3 – Dual-history summarization (keep full UI history)

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

## Phase 4 – Frontend integration with summaries

- **Expose summary in thread values**
  - Ensure `summary_history` is part of `AgentThreadState.values` returned over the LangGraph API.
- **Optional: Visual marker for summarization**
  - In `MessageList`, if `summary_history` exists:
    - Insert a small “Earlier context summarized” system chip between older and newer messages.
    - Display a collapsible block with the summary text if the user expands it.
  - Keep the full raw messages rendered as today so UX does not regress.

## Phase 5 – Testing, observability, and docs

- **Backend tests**
  - Add unit tests around the new middleware:
    - When token thresholds are exceeded, `summary_history` is populated.
    - `messages` continues to hold all prior turns.
    - Model input in LangSmith traces shows summary + recent messages only.
- **Manual QA**
  - Long, multi-turn chats to verify:
    - UI still shows full history.
    - Summaries appear only when conversations are long.
    - No regressions in uploads, RAG tools, or artifacts.
- **Documentation**
  - Update root `README.md` with:
    - Note about GCP Postgres persistence.
    - Note about LangSmith tracing.
  - Update `deer-flow/backend/CLAUDE.md` with:
    - Description of the new UI-preserving summarization middleware.
    - How to tune or disable summarization via `config.yaml`.

