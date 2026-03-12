# RAG (Milvus) — Upload Indexing and Retrieval

This project includes a Milvus-backed vector RAG pipeline to retrieve relevant passages from a thread’s uploaded documents.

## What it does

- Uploads (PDF/DOC/PPT/etc.) are converted to Markdown via `markitdown` (see `src/gateway/routers/uploads.py`).
- The vector RAG tools index `.md`/`.txt` files from the thread’s uploads directory:
  - `/mnt/user-data/uploads/` (virtual path seen by agent)
  - Host path: `backend/.deer-flow/threads/{thread_id}/user-data/uploads/`
- Indexing is **best-effort auto-triggered** after uploads via FastAPI background tasks.

## Tools

- `rag_ingest_uploads_vector(thread_id)`
  - Chunks upload markdown into passages, embeds each passage, upserts into Milvus.
- `rag_search_vector(thread_id, query, k=6)`
  - Embeds the query and searches Milvus (filtered by `thread_id`), returning top-k passages with citation fields.

Tool implementations live at:
- `src/community/rag_milvus/tools.py`
- `src/community/rag_milvus/utils.py`

## Configuration (env)

Set these in `deer-flow/.env` (or your environment):

- `MILVUS_URI` (required for vector RAG)
  - Example: `http://localhost:19530`
- `MILVUS_TOKEN` (optional, depends on your Milvus deployment)
- `EMBEDDINGS_BASE_URL` (optional; only needed for OpenAI-compatible gateways)
  - For DeepSeek-compatible API: `https://api.deepseek.com/v1`
- `EMBEDDINGS_API_KEY` (required for vector RAG)
- `EMBEDDINGS_MODEL` (required; provider-specific embedding model name)

The tool configs in `deer-flow/config.yaml` reference these env vars.

## Local Milvus (Docker)

Use any standard Milvus standalone docker setup. Once Milvus is reachable at `MILVUS_URI`, vector RAG indexing and search will work.

## Citations

Each retrieved chunk includes:
- `virtual_path` (e.g. `/mnt/user-data/uploads/report.md`)
- `chunk_id` (stable/idempotent id used for upsert)

Use these in “Methodology & Sources”.

