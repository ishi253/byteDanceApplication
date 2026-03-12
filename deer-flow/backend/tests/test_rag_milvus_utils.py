from pathlib import Path

from src.community.rag_milvus.utils import chunk_text, stable_chunk_id


def test_chunk_text_is_deterministic_and_nonempty():
    text = "\n\n".join([f"para {i} " + ("x" * 250) for i in range(10)])
    a = chunk_text(text, max_chars=800, min_chars=200)
    b = chunk_text(text, max_chars=800, min_chars=200)
    assert a == b
    assert len(a) > 0
    assert all(isinstance(c, str) and c.strip() for c in a)


def test_stable_chunk_id_changes_with_content():
    fp = Path("report.md")
    id1 = stable_chunk_id(thread_id="t1", file_path=fp, chunk_index=0, text="hello")
    id2 = stable_chunk_id(thread_id="t1", file_path=fp, chunk_index=0, text="hello")
    id3 = stable_chunk_id(thread_id="t1", file_path=fp, chunk_index=0, text="hello!")
    assert id1 == id2
    assert id1 != id3

