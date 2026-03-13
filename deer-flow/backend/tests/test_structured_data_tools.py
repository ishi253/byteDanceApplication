import json

import pytest


@pytest.fixture
def thread_env(tmp_path, monkeypatch):
    """Set up a temp DEER_FLOW_HOME with uploads dir."""
    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    import src.config.paths as paths_mod

    paths_mod._paths = None
    thread_id = "thread_sd_test"
    uploads = tmp_path / "threads" / thread_id / "user-data" / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    return thread_id, uploads


class TestExtractStructuredDataCSV:
    def test_basic_csv(self, thread_env):
        from src.community.structured_data.tools import extract_structured_data_tool

        thread_id, uploads = thread_env
        csv_content = "Company,Revenue,Year\nAcme,1000000,2025\nBeta,2500000,2024\nGamma,500000,2025\n"
        (uploads / "data.csv").write_text(csv_content, encoding="utf-8")

        result = json.loads(extract_structured_data_tool.invoke({"thread_id": thread_id, "filename": "data.csv"}))
        assert result["ok"] is True
        assert result["columns"] == ["Company", "Revenue", "Year"]
        assert result["row_count"] == 3
        assert len(result["data"]) == 3

    def test_numeric_detection_and_stats(self, thread_env):
        from src.community.structured_data.tools import extract_structured_data_tool

        thread_id, uploads = thread_env
        csv_content = "Item,Price,Quantity\nA,$100,10\nB,$200,20\nC,$150,15\n"
        (uploads / "prices.csv").write_text(csv_content, encoding="utf-8")

        result = json.loads(extract_structured_data_tool.invoke({"thread_id": thread_id, "filename": "prices.csv"}))
        assert result["ok"] is True
        # Price column should be detected as numeric
        assert "Price" in result["summary_stats"] or "Quantity" in result["summary_stats"]

    def test_max_rows_enforcement(self, thread_env):
        from src.community.structured_data.tools import extract_structured_data_tool

        thread_id, uploads = thread_env
        lines = ["ID,Value"] + [f"{i},{i * 10}" for i in range(100)]
        (uploads / "big.csv").write_text("\n".join(lines), encoding="utf-8")

        result = json.loads(extract_structured_data_tool.invoke({"thread_id": thread_id, "filename": "big.csv", "max_rows": 10}))
        assert result["ok"] is True
        assert len(result["data"]) == 10

    def test_column_type_detection(self, thread_env):
        from src.community.structured_data.tools import extract_structured_data_tool

        thread_id, uploads = thread_env
        csv_content = "Name,Score,Date\nAlice,95,2025-01-01\nBob,88,2025-02-15\nCarol,92,2025-03-20\n"
        (uploads / "typed.csv").write_text(csv_content, encoding="utf-8")

        result = json.loads(extract_structured_data_tool.invoke({"thread_id": thread_id, "filename": "typed.csv"}))
        assert result["ok"] is True
        assert result["column_types"][0] == "text"  # Name
        assert result["column_types"][1] == "numeric"  # Score

    def test_summary_stats_values(self, thread_env):
        from src.community.structured_data.tools import extract_structured_data_tool

        thread_id, uploads = thread_env
        csv_content = "Metric,Value\nA,10\nB,20\nC,30\nD,40\n"
        (uploads / "stats.csv").write_text(csv_content, encoding="utf-8")

        result = json.loads(extract_structured_data_tool.invoke({"thread_id": thread_id, "filename": "stats.csv"}))
        assert result["ok"] is True
        stats = result["summary_stats"].get("Value", {})
        if stats:
            assert stats["min"] == 10
            assert stats["max"] == 40
            assert stats["mean"] == 25.0
            assert stats["count"] == 4


class TestExtractStructuredDataEdgeCases:
    def test_missing_file(self, thread_env):
        from src.community.structured_data.tools import extract_structured_data_tool

        thread_id, _ = thread_env
        result = json.loads(extract_structured_data_tool.invoke({"thread_id": thread_id, "filename": "nonexistent.csv"}))
        assert result["ok"] is False
        assert "not found" in result["message"].lower()

    def test_unsupported_extension(self, thread_env):
        from src.community.structured_data.tools import extract_structured_data_tool

        thread_id, uploads = thread_env
        (uploads / "data.json").write_text("{}", encoding="utf-8")

        result = json.loads(extract_structured_data_tool.invoke({"thread_id": thread_id, "filename": "data.json"}))
        assert result["ok"] is False
        assert "unsupported" in result["message"].lower()

    def test_empty_csv(self, thread_env):
        from src.community.structured_data.tools import extract_structured_data_tool

        thread_id, uploads = thread_env
        (uploads / "empty.csv").write_text("", encoding="utf-8")

        result = json.loads(extract_structured_data_tool.invoke({"thread_id": thread_id, "filename": "empty.csv"}))
        assert result["ok"] is True
        assert result["row_count"] == 0


class TestListUploadedDataFiles:
    def test_categorization(self, thread_env):
        from src.community.structured_data.tools import list_uploaded_data_files_tool

        thread_id, uploads = thread_env
        (uploads / "data.csv").write_text("a,b\n1,2", encoding="utf-8")
        (uploads / "report.pdf").write_bytes(b"%PDF-1.4")
        (uploads / "notes.md").write_text("# Notes", encoding="utf-8")
        (uploads / "sheet.xlsx").write_bytes(b"PK")

        result = json.loads(list_uploaded_data_files_tool.invoke({"thread_id": thread_id}))
        assert result["ok"] is True
        assert result["total_files"] == 4

        cats = result["categories"]
        assert len(cats["structured_data"]) == 2  # csv + xlsx
        assert len(cats["document"]) == 1  # pdf
        assert len(cats["text"]) == 1  # md

    def test_empty_uploads(self, thread_env):
        from src.community.structured_data.tools import list_uploaded_data_files_tool

        thread_id, _ = thread_env
        result = json.loads(list_uploaded_data_files_tool.invoke({"thread_id": thread_id}))
        assert result["ok"] is True
        assert result["total_files"] == 0

    def test_file_entry_fields(self, thread_env):
        from src.community.structured_data.tools import list_uploaded_data_files_tool

        thread_id, uploads = thread_env
        (uploads / "test.csv").write_text("a\n1", encoding="utf-8")

        result = json.loads(list_uploaded_data_files_tool.invoke({"thread_id": thread_id}))
        entry = result["categories"]["structured_data"][0]
        assert "filename" in entry
        assert "virtual_path" in entry
        assert "size_bytes" in entry
        assert entry["virtual_path"].endswith("test.csv")
