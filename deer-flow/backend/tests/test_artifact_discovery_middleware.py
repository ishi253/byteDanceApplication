"""Tests for ArtifactDiscoveryMiddleware."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.agents.middlewares.artifact_discovery_middleware import (
    OUTPUTS_VIRTUAL_PREFIX,
    ArtifactDiscoveryMiddleware,
)


def _make_state(outputs_path: str, artifacts: list[str] | None = None):
    return {
        "messages": [],
        "thread_data": {
            "workspace_path": "/tmp/ws",
            "uploads_path": "/tmp/up",
            "outputs_path": outputs_path,
        },
        "artifacts": artifacts or [],
    }


class TestArtifactDiscoveryMiddleware:
    def test_discovers_new_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "report.md").write_text("# Report")
            (Path(tmpdir) / "data_summary.md").write_text("# Data Summary")

            middleware = ArtifactDiscoveryMiddleware()
            state = _make_state(tmpdir)
            result = middleware.after_agent(state, runtime=MagicMock())

            assert result is not None
            assert len(result["artifacts"]) == 2
            expected = {
                f"{OUTPUTS_VIRTUAL_PREFIX}/data_summary.md",
                f"{OUTPUTS_VIRTUAL_PREFIX}/report.md",
            }
            assert set(result["artifacts"]) == expected

    def test_skips_already_tracked_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "report.md").write_text("# Report")
            (Path(tmpdir) / "analysis.md").write_text("# Analysis")

            middleware = ArtifactDiscoveryMiddleware()
            state = _make_state(
                tmpdir,
                artifacts=[f"{OUTPUTS_VIRTUAL_PREFIX}/report.md"],
            )
            result = middleware.after_agent(state, runtime=MagicMock())

            assert result is not None
            assert result["artifacts"] == [f"{OUTPUTS_VIRTUAL_PREFIX}/analysis.md"]

    def test_returns_none_when_no_new_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "report.md").write_text("# Report")

            middleware = ArtifactDiscoveryMiddleware()
            state = _make_state(
                tmpdir,
                artifacts=[f"{OUTPUTS_VIRTUAL_PREFIX}/report.md"],
            )
            result = middleware.after_agent(state, runtime=MagicMock())

            assert result is None

    def test_returns_none_when_outputs_dir_missing(self):
        middleware = ArtifactDiscoveryMiddleware()
        state = _make_state("/nonexistent/path")
        result = middleware.after_agent(state, runtime=MagicMock())

        assert result is None

    def test_returns_none_when_thread_data_missing(self):
        middleware = ArtifactDiscoveryMiddleware()
        state = {"messages": [], "artifacts": []}
        result = middleware.after_agent(state, runtime=MagicMock())

        assert result is None

    def test_returns_none_when_outputs_path_empty(self):
        middleware = ArtifactDiscoveryMiddleware()
        state = _make_state("")
        result = middleware.after_agent(state, runtime=MagicMock())

        assert result is None

    def test_discovers_files_in_subdirectories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "charts"
            subdir.mkdir()
            (subdir / "market_share.png").write_bytes(b"\x89PNG")
            (Path(tmpdir) / "report.md").write_text("# Report")

            middleware = ArtifactDiscoveryMiddleware()
            state = _make_state(tmpdir)
            result = middleware.after_agent(state, runtime=MagicMock())

            assert result is not None
            expected = {
                f"{OUTPUTS_VIRTUAL_PREFIX}/charts/market_share.png",
                f"{OUTPUTS_VIRTUAL_PREFIX}/report.md",
            }
            assert set(result["artifacts"]) == expected

    def test_ignores_directories_not_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "empty_dir"
            subdir.mkdir()

            middleware = ArtifactDiscoveryMiddleware()
            state = _make_state(tmpdir)
            result = middleware.after_agent(state, runtime=MagicMock())

            assert result is None

    def test_empty_outputs_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            middleware = ArtifactDiscoveryMiddleware()
            state = _make_state(tmpdir)
            result = middleware.after_agent(state, runtime=MagicMock())

            assert result is None

    def test_mixed_tracked_and_untracked(self):
        """Some files tracked, some not — only untracked ones are returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["a.md", "b.csv", "c.html", "d.json"]:
                (Path(tmpdir) / name).write_text(name)

            middleware = ArtifactDiscoveryMiddleware()
            state = _make_state(
                tmpdir,
                artifacts=[
                    f"{OUTPUTS_VIRTUAL_PREFIX}/a.md",
                    f"{OUTPUTS_VIRTUAL_PREFIX}/c.html",
                ],
            )
            result = middleware.after_agent(state, runtime=MagicMock())

            assert result is not None
            assert set(result["artifacts"]) == {
                f"{OUTPUTS_VIRTUAL_PREFIX}/b.csv",
                f"{OUTPUTS_VIRTUAL_PREFIX}/d.json",
            }
