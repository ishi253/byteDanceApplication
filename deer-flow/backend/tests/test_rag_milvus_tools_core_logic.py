import json

import pytest


class _FakeEmbeddings:
    def embed_query(self, text: str):
        # fixed dim vector
        return [0.0, 0.1, 0.2]


class _FakeHit:
    def __init__(self, distance: float, entity: dict):
        self.distance = distance
        self.entity = entity


class _FakeMilvusClient:
    def __init__(self, *args, **kwargs):
        self._collections = set()
        self._rows = []

    def has_collection(self, name: str) -> bool:
        return name in self._collections

    def create_collection(self, **kwargs):
        self._collections.add(kwargs["collection_name"])

    def upsert(self, collection_name: str, data: list[dict]):
        self._collections.add(collection_name)
        self._rows.extend(data)

    def search(self, collection_name: str, data, limit: int, filter: str, output_fields):
        # Return first `limit` rows matching thread_id filter
        # filter is: thread_id == '...'
        thread_id = filter.split("'")[1]
        matches = [r for r in self._rows if r.get("thread_id") == thread_id]
        hits = [
            _FakeHit(
                0.123,
                {
                    "id": r["id"],
                    "thread_id": r["thread_id"],
                    "filename": r["filename"],
                    "virtual_path": r["virtual_path"],
                    "text": r["text"],
                    "source_type": r.get("source_type"),
                },
            )
            for r in matches[:limit]
        ]
        return [hits]


@pytest.fixture
def uploads_dir(tmp_path, monkeypatch):
    # Point DeerFlow Paths.base_dir to tmp so sandbox_uploads_dir(thread) is under tmp.
    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    thread_id = "thread_123"
    d = tmp_path / "threads" / thread_id / "user-data" / "uploads"
    d.mkdir(parents=True, exist_ok=True)
    (d / "a.md").write_text("This is a test paragraph.\n\n" + ("x" * 300), encoding="utf-8")
    return thread_id, d


def test_vector_ingest_and_search_without_real_milvus(monkeypatch, uploads_dir):
    thread_id, _ = uploads_dir

    # Patch tool config access to return required fields.
    from src.community.rag_milvus import tools as rag_tools
    fake_milvus = _FakeMilvusClient()

    def fake_get_tool_cfg(name: str) -> dict:
        return {
            "milvus_uri": "http://fake:19530",
            "collection_name": "test_collection",
            "embeddings_api_key": "test",
            "embeddings_model": "fake-embed",
            "chunk_max_chars": 800,
            "chunk_min_chars": 200,
        }

    monkeypatch.setattr(rag_tools, "_get_tool_cfg", fake_get_tool_cfg)
    monkeypatch.setattr(rag_tools, "_get_milvus_client", lambda tool_name: fake_milvus)
    monkeypatch.setattr(rag_tools, "_get_embeddings", lambda tool_name: _FakeEmbeddings())

    ingest_json = rag_tools.rag_ingest_uploads_vector_tool.invoke({"thread_id": thread_id})
    ingest = json.loads(ingest_json)
    assert ingest["ok"] is True
    assert ingest["chunks_indexed"] >= 1

    search_json = rag_tools.rag_search_vector_tool.invoke({"thread_id": thread_id, "query": "test", "k": 3})
    search = json.loads(search_json)
    assert search["ok"] is True
    assert len(search["results"]) >= 1
    assert search["results"][0]["virtual_path"].endswith("a.md")

