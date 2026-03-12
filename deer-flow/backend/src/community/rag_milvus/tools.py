import json
import time
from pathlib import Path

from langchain.tools import tool
from langchain_openai import OpenAIEmbeddings
from pymilvus import MilvusClient

from src.config import get_app_config
from src.config.paths import VIRTUAL_PATH_PREFIX, get_paths

from .utils import chunk_text, stable_chunk_id


def _get_tool_cfg(tool_name: str) -> dict:
    cfg = get_app_config().get_tool_config(tool_name)
    if cfg is None:
        return {}
    return dict(cfg.model_extra or {})


def _get_milvus_client(tool_name: str) -> MilvusClient:
    cfg = _get_tool_cfg(tool_name)
    uri = cfg.get("milvus_uri")
    if not uri:
        raise ValueError("Missing milvus_uri. Set MILVUS_URI in .env and ensure the tool config includes milvus_uri: $MILVUS_URI.")
    token = cfg.get("milvus_token")
    return MilvusClient(uri=uri, token=token) if token else MilvusClient(uri=uri)


def _get_collection_name(tool_name: str) -> str:
    cfg = _get_tool_cfg(tool_name)
    return str(cfg.get("collection_name") or "deerflow_rag_chunks")


def _get_embeddings(tool_name: str) -> OpenAIEmbeddings:
    cfg = _get_tool_cfg(tool_name)
    base_url = cfg.get("embeddings_base_url")
    api_key = cfg.get("embeddings_api_key")
    model = cfg.get("embeddings_model")

    if not api_key:
        raise ValueError("Missing embeddings_api_key. Set EMBEDDINGS_API_KEY (or reuse DEEPSEEK_API_KEY) in .env and ensure tool config includes embeddings_api_key.")
    if not model:
        raise ValueError("Missing embeddings_model. Set EMBEDDINGS_MODEL in .env (provider-specific).")

    # OpenAI-compatible embeddings client (works with gateways that implement the OpenAI API shape).
    # For DeepSeek-compatible setups, set base_url=https://api.deepseek.com/v1.
    kwargs = {"api_key": api_key, "model": model}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAIEmbeddings(**kwargs)


def _ensure_collection(client: MilvusClient, collection_name: str, dim: int) -> None:
    if client.has_collection(collection_name):
        return
    # Create a collection with dynamic fields enabled so we can store metadata like filename/text.
    client.create_collection(
        collection_name=collection_name,
        dimension=dim,
        metric_type="COSINE",
        consistency_level="Session",
        enable_dynamic_field=True,
    )


def _list_upload_text_files(uploads_dir: Path) -> list[Path]:
    # Prefer converted markdown.
    return sorted([p for p in uploads_dir.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".txt"}])


@tool("rag_ingest_uploads_vector", parse_docstring=True)
def rag_ingest_uploads_vector_tool(thread_id: str) -> str:
    """Index a thread's uploaded documents into Milvus for semantic retrieval.

    Reads `.md`/`.txt` files under `/mnt/user-data/uploads/` (thread scoped),
    chunks them, embeds chunks, then upserts into Milvus with deterministic ids.

    Args:
        thread_id: Current thread id.
    """
    t0 = time.time()
    paths = get_paths()
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    files = _list_upload_text_files(uploads_dir)
    if not files:
        return json.dumps(
            {
                "ok": False,
                "message": "No .md/.txt files found in uploads. Upload a PDF/DOC/PPT and DeerFlow will convert it to .md, then re-run ingest.",
                "uploads_dir": str(uploads_dir),
            },
            ensure_ascii=False,
            indent=2,
        )

    client = _get_milvus_client("rag_ingest_uploads_vector")
    collection = _get_collection_name("rag_ingest_uploads_vector")
    embeddings = _get_embeddings("rag_ingest_uploads_vector")

    # Determine embedding dim once (query embedding shape).
    probe = embeddings.embed_query("dimension probe")
    dim = len(probe)
    _ensure_collection(client, collection, dim)

    max_chars = int(_get_tool_cfg("rag_ingest_uploads_vector").get("chunk_max_chars") or 1400)
    min_chars = int(_get_tool_cfg("rag_ingest_uploads_vector").get("chunk_min_chars") or 200)

    rows = []
    chunk_count = 0
    file_names = []

    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            continue
        if not text:
            continue

        file_names.append(fp.name)
        chunks = chunk_text(text, max_chars=max_chars, min_chars=min_chars)
        for idx, ch_text in enumerate(chunks):
            chunk_id = stable_chunk_id(thread_id=thread_id, file_path=fp, chunk_index=idx, text=ch_text)
            vec = embeddings.embed_query(ch_text)
            rows.append(
                {
                    "id": chunk_id,
                    "vector": vec,
                    "thread_id": thread_id,
                    "filename": fp.name,
                    "virtual_path": f"{VIRTUAL_PATH_PREFIX}/uploads/{fp.name}",
                    "text": ch_text,
                    "source_type": "upload",
                }
            )
            chunk_count += 1

    if not rows:
        return json.dumps({"ok": False, "message": "No chunks produced from uploads."}, ensure_ascii=False, indent=2)

    client.upsert(collection_name=collection, data=rows)

    return json.dumps(
        {
            "ok": True,
            "message": "Indexed uploads into Milvus (vector RAG).",
            "collection": collection,
            "files_indexed": sorted(set(file_names)),
            "chunks_indexed": chunk_count,
            "elapsed_seconds": round(time.time() - t0, 3),
        },
        ensure_ascii=False,
        indent=2,
    )


@tool("rag_search_vector", parse_docstring=True)
def rag_search_vector_tool(thread_id: str, query: str, k: int = 6) -> str:
    """Semantic retrieval from Milvus over a thread's indexed uploads.

    Args:
        thread_id: Current thread id.
        query: Query string to search for.
        k: Number of chunks to return.
    """
    query = (query or "").strip()
    if not query:
        return json.dumps({"ok": False, "message": "Empty query."}, ensure_ascii=False, indent=2)

    client = _get_milvus_client("rag_search_vector")
    collection = _get_collection_name("rag_search_vector")
    embeddings = _get_embeddings("rag_search_vector")

    qvec = embeddings.embed_query(query)
    if not client.has_collection(collection):
        return json.dumps(
            {"ok": False, "message": "Collection not found. Run rag_ingest_uploads_vector first.", "collection": collection},
            ensure_ascii=False,
            indent=2,
        )

    results = client.search(
        collection_name=collection,
        data=[qvec],
        limit=max(1, int(k)),
        filter=f"thread_id == '{thread_id}'",
        output_fields=["id", "thread_id", "filename", "virtual_path", "text", "source_type"],
    )

    # pymilvus returns list per query; we only pass one query vector
    hits = results[0] if results else []
    normalized = []
    for h in hits:
        entity = getattr(h, "entity", {}) or {}
        normalized.append(
            {
                "score": float(getattr(h, "distance", 0.0)),
                "chunk_id": entity.get("id") or getattr(h, "id", None),
                "filename": entity.get("filename"),
                "virtual_path": entity.get("virtual_path"),
                "text": (entity.get("text") or "")[:1600],
                "source_type": entity.get("source_type"),
            }
        )

    return json.dumps(
        {"ok": True, "query": query, "k": k, "collection": collection, "results": normalized},
        ensure_ascii=False,
        indent=2,
    )

