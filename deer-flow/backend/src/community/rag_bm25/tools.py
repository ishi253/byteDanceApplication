import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain.tools import tool

from src.config.paths import VIRTUAL_PATH_PREFIX, get_paths

_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-\.]{1,}")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _chunk_text(text: str, *, max_chars: int = 1400, min_chars: int = 200) -> list[str]:
    """
    Chunk markdown-ish text into retrieval units without external deps.

    Strategy:
    - split on blank lines
    - greedily pack paragraphs until max_chars
    """
    paras = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    chunks: list[str] = []
    buf: list[str] = []
    size = 0
    for p in paras:
    # If a single paragraph is huge, hard-split it.
        if len(p) > max_chars:
            if buf:
                chunks.append("\n\n".join(buf))
                buf, size = [], 0
            for i in range(0, len(p), max_chars):
                part = p[i : i + max_chars].strip()
                if part:
                    chunks.append(part)
            continue

        if size + len(p) + (2 if buf else 0) > max_chars:
            if buf:
                chunks.append("\n\n".join(buf))
            buf, size = [p], len(p)
        else:
            buf.append(p)
            size += len(p) + (2 if buf else 0)

    if buf:
        chunks.append("\n\n".join(buf))

    # Drop tiny chunks (often headings) unless that would drop everything.
    filtered = [c for c in chunks if len(c) >= min_chars]
    return filtered if filtered else chunks


def _thread_rag_dir(thread_id: str) -> Path:
    return get_paths().thread_dir(thread_id) / "rag"


def _index_path(thread_id: str) -> Path:
    return _thread_rag_dir(thread_id) / "bm25_index.json"


@dataclass(frozen=True)
class _Chunk:
    chunk_id: str
    filename: str
    virtual_path: str
    text: str
    tokens: list[str]


def _build_bm25(chunks: list[_Chunk]) -> dict[str, Any]:
    # Document frequency per term
    df: dict[str, int] = {}
    # Term frequencies per doc
    tfs: list[dict[str, int]] = []
    doc_lens: list[int] = []

    for ch in chunks:
        tf: dict[str, int] = {}
        for tok in ch.tokens:
            tf[tok] = tf.get(tok, 0) + 1
        tfs.append(tf)
        doc_lens.append(len(ch.tokens))
        for tok in set(ch.tokens):
            df[tok] = df.get(tok, 0) + 1

    n_docs = len(chunks)
    avgdl = (sum(doc_lens) / n_docs) if n_docs else 0.0

    return {
        "version": 1,
        "n_docs": n_docs,
        "avgdl": avgdl,
        "df": df,
        "doc_lens": doc_lens,
        "tfs": tfs,
        "chunks": [
            {
                "chunk_id": ch.chunk_id,
                "filename": ch.filename,
                "virtual_path": ch.virtual_path,
                "text": ch.text,
            }
            for ch in chunks
        ],
    }


def _bm25_scores(index: dict[str, Any], query_tokens: list[str], *, k1: float = 1.5, b: float = 0.75) -> list[float]:
    n_docs = int(index.get("n_docs", 0))
    if n_docs == 0:
        return []

    df: dict[str, int] = index["df"]
    avgdl: float = float(index["avgdl"])
    doc_lens: list[int] = index["doc_lens"]
    tfs: list[dict[str, int]] = index["tfs"]

    # query term frequencies (slight boost for repeated query terms)
    qtf: dict[str, int] = {}
    for t in query_tokens:
        qtf[t] = qtf.get(t, 0) + 1

    scores = [0.0] * n_docs
    for term, qcount in qtf.items():
        n_q = df.get(term, 0)
        if n_q <= 0:
            continue
        # BM25 idf (with +1 to keep positive)
        idf = math.log(1.0 + (n_docs - n_q + 0.5) / (n_q + 0.5))
        for i in range(n_docs):
            f = tfs[i].get(term, 0)
            if f <= 0:
                continue
            dl = doc_lens[i]
            denom = f + k1 * (1.0 - b + b * (dl / avgdl if avgdl > 0 else 0.0))
            score = idf * (f * (k1 + 1.0)) / (denom if denom else 1.0)
            # small multiplier for repeated query terms
            scores[i] += score * (1.0 + 0.1 * (qcount - 1))
    return scores


def _load_index(thread_id: str) -> dict[str, Any] | None:
    p = _index_path(thread_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


@tool("rag_ingest_uploads", parse_docstring=True)
def rag_ingest_uploads_tool(thread_id: str) -> str:
    """Index a thread's uploaded documents for retrieval (prototype RAG).

    This builds a lightweight BM25 index over uploaded markdown/text files in
    `/mnt/user-data/uploads/` (thread-scoped), chunking them into passages.

    Args:
        thread_id: The current thread id.
    """
    paths = get_paths()
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Prefer converted markdown when present.
    candidates = sorted([p for p in uploads_dir.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".txt"}])
    if not candidates:
        return json.dumps(
            {
                "ok": False,
                "message": "No .md/.txt files found in uploads. Upload a PDF/DOC/PPT and DeerFlow will convert it to .md, then re-run ingest.",
                "uploads_dir": str(uploads_dir),
            },
            ensure_ascii=False,
            indent=2,
        )

    chunks: list[_Chunk] = []
    for file_path in candidates:
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            continue
        if not text:
            continue

        for j, ch_text in enumerate(_chunk_text(text)):
            toks = _tokenize(ch_text)
            if not toks:
                continue
            chunks.append(
                _Chunk(
                    chunk_id=f"{file_path.name}::chunk{j}",
                    filename=file_path.name,
                    virtual_path=f"{VIRTUAL_PATH_PREFIX}/uploads/{file_path.name}",
                    text=ch_text,
                    tokens=toks,
                )
            )

    rag_dir = _thread_rag_dir(thread_id)
    rag_dir.mkdir(parents=True, exist_ok=True)
    index = _build_bm25(chunks)
    _index_path(thread_id).write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")

    return json.dumps(
        {
            "ok": True,
            "message": "Indexed uploads for retrieval (BM25 prototype).",
            "files_indexed": sorted({c["filename"] for c in index["chunks"]}),
            "chunks_indexed": index["n_docs"],
            "index_path": str(_index_path(thread_id)),
        },
        ensure_ascii=False,
        indent=2,
    )


@tool("rag_search", parse_docstring=True)
def rag_search_tool(thread_id: str, query: str, k: int = 6) -> str:
    """Retrieve relevant passages from indexed uploaded documents (prototype RAG).

    Use `rag_ingest_uploads` first (or re-run it after new uploads).

    Args:
        thread_id: The current thread id.
        query: What you want to find in the uploaded documents.
        k: Number of passages to return.
    """
    query = (query or "").strip()
    if not query:
        return json.dumps({"ok": False, "message": "Empty query."}, ensure_ascii=False, indent=2)

    index = _load_index(thread_id)
    if index is None:
        return json.dumps(
            {
                "ok": False,
                "message": "No index found. Run rag_ingest_uploads first.",
                "expected_index_path": str(_index_path(thread_id)),
            },
            ensure_ascii=False,
            indent=2,
        )

    q_tokens = _tokenize(query)
    if not q_tokens:
        return json.dumps({"ok": False, "message": "Query had no searchable tokens."}, ensure_ascii=False, indent=2)

    scores = _bm25_scores(index, q_tokens)
    chunks = index.get("chunks", [])

    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    results = []
    for i in ranked[: max(1, int(k))]:
        if scores[i] <= 0:
            continue
        ch = chunks[i]
        results.append(
            {
                "score": round(float(scores[i]), 6),
                "chunk_id": ch["chunk_id"],
                "filename": ch["filename"],
                "virtual_path": ch["virtual_path"],
                "text": ch["text"][:1600],
            }
        )

    return json.dumps(
        {
            "ok": True,
            "query": query,
            "k": k,
            "results": results,
        },
        ensure_ascii=False,
        indent=2,
    )

