import json

import pytest


@pytest.fixture
def thread_env(tmp_path, monkeypatch):
    """Set up a temp DEER_FLOW_HOME and return thread_id."""
    monkeypatch.setenv("DEER_FLOW_HOME", str(tmp_path))
    # Reset the paths singleton so it picks up the new env
    import src.config.paths as paths_mod

    paths_mod._paths = None
    thread_id = "thread_fc_test"
    return thread_id


class TestStoreDataPoint:
    def test_creates_file_and_stores(self, thread_env):
        from src.community.fact_check.tools import store_data_point_tool

        result = json.loads(
            store_data_point_tool.invoke(
                {
                    "thread_id": thread_env,
                    "section": "market_sizing",
                    "field": "TAM",
                    "value": "$5.2B",
                    "source_url": "https://example.com/report",
                    "source_name": "Gartner 2025",
                    "source_date": "2025-06",
                    "confidence": "high",
                }
            )
        )
        assert result["ok"] is True
        assert result["id"].startswith("dp_")
        assert result["total_data_points"] == 1

    def test_generates_unique_ids(self, thread_env):
        from src.community.fact_check.tools import store_data_point_tool

        ids = set()
        for i in range(5):
            result = json.loads(
                store_data_point_tool.invoke(
                    {
                        "thread_id": thread_env,
                        "section": "competitive",
                        "field": f"share_{i}",
                        "value": f"{i * 10}%",
                        "source_url": f"https://example.com/{i}",
                        "source_name": f"Source {i}",
                    }
                )
            )
            ids.add(result["id"])
        assert len(ids) == 5

    def test_appends_to_existing(self, thread_env):
        from src.community.fact_check.tools import store_data_point_tool

        store_data_point_tool.invoke(
            {
                "thread_id": thread_env,
                "section": "market_sizing",
                "field": "TAM",
                "value": "$5B",
                "source_url": "https://a.com",
                "source_name": "Source A",
            }
        )
        result = json.loads(
            store_data_point_tool.invoke(
                {
                    "thread_id": thread_env,
                    "section": "market_sizing",
                    "field": "SAM",
                    "value": "$2B",
                    "source_url": "https://b.com",
                    "source_name": "Source B",
                }
            )
        )
        assert result["total_data_points"] == 2

    def test_defaults_confidence_and_source_type(self, thread_env):
        from src.community.fact_check.tools import _load_data_points, store_data_point_tool

        store_data_point_tool.invoke(
            {
                "thread_id": thread_env,
                "section": "trends",
                "field": "growth",
                "value": "12%",
                "source_url": "https://x.com",
                "source_name": "X",
            }
        )
        dp = _load_data_points(thread_env)["data_points"][0]
        assert dp["confidence"] == "medium"
        assert dp["source_type"] == "web"

    def test_invalid_confidence_defaults_to_medium(self, thread_env):
        from src.community.fact_check.tools import _load_data_points, store_data_point_tool

        store_data_point_tool.invoke(
            {
                "thread_id": thread_env,
                "section": "trends",
                "field": "growth",
                "value": "12%",
                "source_url": "https://x.com",
                "source_name": "X",
                "confidence": "invalid",
            }
        )
        dp = _load_data_points(thread_env)["data_points"][0]
        assert dp["confidence"] == "medium"


class TestFactCheck:
    def _store(self, thread_id, section, field, value, source_name, source_date="2025-06", confidence="medium"):
        from src.community.fact_check.tools import store_data_point_tool

        store_data_point_tool.invoke(
            {
                "thread_id": thread_id,
                "section": section,
                "field": field,
                "value": value,
                "source_url": f"https://{source_name.lower().replace(' ', '')}.com",
                "source_name": source_name,
                "source_date": source_date,
                "confidence": confidence,
            }
        )

    def test_empty_store(self, thread_env):
        from src.community.fact_check.tools import fact_check_tool

        result = json.loads(fact_check_tool.invoke({"thread_id": thread_env}))
        assert result["ok"] is True
        assert result["total_data_points"] == 0
        assert result["issues"] == []
        assert "summary" in result
        assert "scanned 0 data point" in result["summary"]

    def test_contradiction_detection(self, thread_env):
        from src.community.fact_check.tools import fact_check_tool

        self._store(thread_env, "market_sizing", "TAM", "$3B", "Source A")
        self._store(thread_env, "market_sizing", "TAM", "$5B", "Source B")

        result = json.loads(fact_check_tool.invoke({"thread_id": thread_env}))
        contradictions = [i for i in result["issues"] if i["type"] == "contradiction"]
        assert len(contradictions) == 1
        assert contradictions[0]["field"] == "TAM"
        assert len(contradictions[0]["values"]) == 2
        assert "Fact check scanned" in result["summary"]

    def test_staleness_detection(self, thread_env):
        from src.community.fact_check.tools import fact_check_tool

        self._store(thread_env, "regulatory", "fine_cap", "$20M", "Old Report", source_date="2023-01")

        result = json.loads(fact_check_tool.invoke({"thread_id": thread_env}))
        stale = [i for i in result["issues"] if i["type"] == "stale_data"]
        assert len(stale) == 1
        assert stale[0]["source_date"] == "2023-01"

    def test_single_source_risk(self, thread_env):
        from src.community.fact_check.tools import fact_check_tool

        self._store(thread_env, "competitive", "share_x", "35%", "Only Source")

        result = json.loads(fact_check_tool.invoke({"thread_id": thread_env}))
        single = [i for i in result["issues"] if i["type"] == "single_source"]
        assert len(single) == 1

    def test_outlier_detection(self, thread_env):
        from src.community.fact_check.tools import fact_check_tool

        # Create enough data points for outlier detection (need >=3)
        self._store(thread_env, "market_sizing", "growth_a", "10%", "S1")
        self._store(thread_env, "market_sizing", "growth_b", "12%", "S2")
        self._store(thread_env, "market_sizing", "growth_c", "11%", "S3")
        self._store(thread_env, "market_sizing", "growth_d", "95%", "S4")  # outlier

        result = json.loads(fact_check_tool.invoke({"thread_id": thread_env}))
        outliers = [i for i in result["issues"] if i["type"] == "outlier"]
        assert len(outliers) >= 1
        outlier_fields = [o["field"] for o in outliers]
        assert "growth_d" in outlier_fields

    def test_non_numeric_outlier_handling(self, thread_env):
        """Non-numeric values should not cause errors in outlier detection."""
        from src.community.fact_check.tools import fact_check_tool

        self._store(thread_env, "competitive", "leader", "Company A", "S1")
        self._store(thread_env, "competitive", "challenger", "Company B", "S2")
        self._store(thread_env, "competitive", "niche", "Company C", "S3")

        result = json.loads(fact_check_tool.invoke({"thread_id": thread_env}))
        outliers = [i for i in result["issues"] if i["type"] == "outlier"]
        assert len(outliers) == 0  # No numeric data, no outliers

    def test_coverage_gap_detection(self, thread_env):
        from src.community.fact_check.tools import fact_check_tool

        # Only store data for market_sizing — all other sections missing
        self._store(thread_env, "market_sizing", "TAM", "$5B", "Source A")

        result = json.loads(fact_check_tool.invoke({"thread_id": thread_env}))
        gaps = [i for i in result["issues"] if i["type"] == "coverage_gap"]
        assert len(gaps) == 1
        assert "competitive" in gaps[0]["missing_sections"]
        assert "regulatory" in gaps[0]["missing_sections"]

    def test_section_filter(self, thread_env):
        from src.community.fact_check.tools import fact_check_tool

        self._store(thread_env, "market_sizing", "TAM", "$5B", "S1")
        self._store(thread_env, "competitive", "share", "35%", "S2")

        result = json.loads(fact_check_tool.invoke({"thread_id": thread_env, "section": "market_sizing"}))
        assert result["total_data_points"] == 1
        # No coverage gap check when filtering by section
        gaps = [i for i in result["issues"] if i["type"] == "coverage_gap"]
        assert len(gaps) == 0

    def test_same_value_duplicates_no_contradiction(self, thread_env):
        from src.community.fact_check.tools import fact_check_tool

        self._store(thread_env, "market_sizing", "TAM", "$5B", "Source A")
        self._store(thread_env, "market_sizing", "TAM", "$5B", "Source B")

        result = json.loads(fact_check_tool.invoke({"thread_id": thread_env}))
        contradictions = [i for i in result["issues"] if i["type"] == "contradiction"]
        assert len(contradictions) == 0

    def test_fact_check_telemetry_written(self, thread_env):
        from src.community.fact_check.tools import (
            _fact_check_telemetry_path,
            fact_check_tool,
        )

        # Run on empty store first to ensure it does not crash.
        json.loads(fact_check_tool.invoke({"thread_id": thread_env}))

        telemetry_path = _fact_check_telemetry_path(thread_env)
        assert telemetry_path.exists()

        raw = telemetry_path.read_text(encoding="utf-8").strip().splitlines()
        assert raw, "Expected at least one telemetry record"
        last_record = json.loads(raw[-1])

        assert last_record["thread_id"] == thread_env
        assert last_record["total_data_points"] == 0
        assert last_record["issues_total"] == 0


class TestGetSourcedData:
    def test_empty_store(self, thread_env):
        from src.community.fact_check.tools import get_sourced_data_tool

        result = json.loads(get_sourced_data_tool.invoke({"thread_id": thread_env}))
        assert result["ok"] is True
        assert result["total_data_points"] == 0

    def test_returns_grouped_data(self, thread_env):
        from src.community.fact_check.tools import get_sourced_data_tool, store_data_point_tool

        store_data_point_tool.invoke(
            {
                "thread_id": thread_env,
                "section": "market_sizing",
                "field": "TAM",
                "value": "$5B",
                "source_url": "https://a.com",
                "source_name": "Source A",
                "source_date": "2025-06",
            }
        )
        store_data_point_tool.invoke(
            {
                "thread_id": thread_env,
                "section": "competitive",
                "field": "share",
                "value": "35%",
                "source_url": "https://b.com",
                "source_name": "Source B",
                "source_date": "2025-03",
            }
        )

        result = json.loads(get_sourced_data_tool.invoke({"thread_id": thread_env}))
        assert result["ok"] is True
        assert result["total_data_points"] == 2
        assert "market_sizing" in result["sections"]
        assert "competitive" in result["sections"]
        # Check citation block
        dp = result["sections"]["market_sizing"][0]
        assert dp["citation"] == "[Source A, 2025-06](https://a.com)"

    def test_filters_by_section(self, thread_env):
        from src.community.fact_check.tools import get_sourced_data_tool, store_data_point_tool

        store_data_point_tool.invoke(
            {
                "thread_id": thread_env,
                "section": "market_sizing",
                "field": "TAM",
                "value": "$5B",
                "source_url": "https://a.com",
                "source_name": "A",
            }
        )
        store_data_point_tool.invoke(
            {
                "thread_id": thread_env,
                "section": "competitive",
                "field": "share",
                "value": "35%",
                "source_url": "https://b.com",
                "source_name": "B",
            }
        )

        result = json.loads(get_sourced_data_tool.invoke({"thread_id": thread_env, "section": "competitive"}))
        assert result["total_data_points"] == 1
        assert "competitive" in result["sections"]
        assert "market_sizing" not in result["sections"]
