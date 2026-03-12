import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    filename: str
    virtual_path: str
    text: str


_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-\.]{1,}")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def chunk_text(text: str, *, max_chars: int = 1400, min_chars: int = 200) -> list[str]:
    """
    Chunk markdown-ish text into retrieval units without external deps.

    Strategy:
    - split on blank lines
    - greedily pack paragraphs until max_chars
    - drop tiny chunks unless that would drop everything
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

    filtered = [c for c in chunks if len(c) >= min_chars]
    return filtered if filtered else chunks


def stable_chunk_id(*, thread_id: str, file_path: Path, chunk_index: int, text: str) -> str:
    """
    Deterministic chunk id for idempotent upserts.
    Includes a hash of the content to naturally change when the source changes.
    """
    h = hashlib.sha1()
    h.update(thread_id.encode("utf-8"))
    h.update(b"\0")
    h.update(file_path.name.encode("utf-8"))
    h.update(b"\0")
    h.update(str(chunk_index).encode("utf-8"))
    h.update(b"\0")
    h.update(text.encode("utf-8", errors="ignore"))
    digest = h.hexdigest()[:16]
    return f"{thread_id}:{file_path.name}:chunk{chunk_index}:{digest}"

