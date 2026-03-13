"""Tests for mermaid validation tool."""

import json

from src.community.mermaid_validate.tools import (
    extract_mermaid_blocks,
    validate_mermaid_syntax_tool,
)


class TestExtractMermaidBlocks:
    def test_extracts_single_block(self):
        md = "# Title\n\n```mermaid\ngraph TD\n  A-->B\n```\n\nSome text."
        blocks = extract_mermaid_blocks(md)
        assert len(blocks) == 1
        assert "graph TD" in blocks[0]

    def test_extracts_multiple_blocks(self):
        md = (
            "```mermaid\ngraph LR\n  A-->B\n```\n"
            "Middle text\n"
            "```mermaid\nsequenceDiagram\n  A->>B: msg\n```\n"
        )
        blocks = extract_mermaid_blocks(md)
        assert len(blocks) == 2

    def test_no_blocks(self):
        md = "# Title\n\nNo diagrams here.\n```python\nprint('hi')\n```\n"
        blocks = extract_mermaid_blocks(md)
        assert blocks == []

    def test_empty_string(self):
        assert extract_mermaid_blocks("") == []


class TestValidateMermaidSyntaxTool:
    def test_valid_simple_flowchart(self):
        diagram = "graph TD\n  A[Start] --> B[End]"
        result = json.loads(validate_mermaid_syntax_tool.invoke({"mermaid_code": diagram}))
        assert result["total_diagrams"] == 1
        # With heuristic validation, a simple flowchart should pass
        if result["validation_method"] == "heuristic":
            assert result["ok"] is True

    def test_invalid_date_decimal(self):
        diagram = "gantt\n  title Plan\n  dateFormat YYYY-MM-DD\n  section A\n  Task :date:203.4, 30d"
        result = json.loads(validate_mermaid_syntax_tool.invoke({"mermaid_code": diagram}))
        # Should be caught by either node or heuristic
        assert result["invalid_count"] >= 1 or result["ok"] is False

    def test_markdown_with_multiple_blocks(self):
        md = (
            "# Report\n\n"
            "```mermaid\ngraph TD\n  A-->B\n```\n\n"
            "```mermaid\ngantt\n  title Plan\n  section A\n  Task :date:8.5, 30d\n```\n"
        )
        result = json.loads(validate_mermaid_syntax_tool.invoke({"mermaid_code": md}))
        assert result["total_diagrams"] == 2
        # Second block has invalid date pattern
        if result["validation_method"] == "heuristic":
            assert result["invalid_count"] >= 1

    def test_response_structure(self):
        diagram = "graph LR\n  X --> Y"
        result = json.loads(validate_mermaid_syntax_tool.invoke({"mermaid_code": diagram}))
        assert "ok" in result
        assert "total_diagrams" in result
        assert "valid_count" in result
        assert "invalid_count" in result
        assert "validation_method" in result
        assert "results" in result
        assert isinstance(result["results"], list)

    def test_empty_input(self):
        result = json.loads(validate_mermaid_syntax_tool.invoke({"mermaid_code": ""}))
        assert result["total_diagrams"] == 0

    def test_recommendation_on_invalid(self):
        diagram = "gantt\n  section S\n  T :date:1.5, 10d"
        result = json.loads(validate_mermaid_syntax_tool.invoke({"mermaid_code": diagram}))
        if not result["ok"]:
            assert "recommendation" in result
            assert "fix" in result["recommendation"].lower() or "table" in result["recommendation"].lower()

    def test_diagram_preview_in_results(self):
        diagram = "graph TD\n  A-->B"
        result = json.loads(validate_mermaid_syntax_tool.invoke({"mermaid_code": diagram}))
        for r in result["results"]:
            assert "diagram_preview" in r
            assert "diagram_index" in r
