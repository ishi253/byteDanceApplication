def test_reviewer_config_registered():
    """Verify fact-check-reviewer is registered in BUILTIN_SUBAGENTS."""
    from src.subagents.builtins import BUILTIN_SUBAGENTS

    assert "fact-check-reviewer" in BUILTIN_SUBAGENTS
    config = BUILTIN_SUBAGENTS["fact-check-reviewer"]
    assert config.name == "fact-check-reviewer"


def test_reviewer_config_fields():
    """Verify config field values."""
    from src.subagents.builtins import BUILTIN_SUBAGENTS

    config = BUILTIN_SUBAGENTS["fact-check-reviewer"]
    assert config.model == "inherit"
    assert config.max_turns == 30
    assert config.timeout_seconds == 600
    assert config.tools is None  # Inherit all tools


def test_reviewer_disallowed_tools():
    """Verify tool permissions — no task, no ask_clarification, no present_files."""
    from src.subagents.builtins import BUILTIN_SUBAGENTS

    config = BUILTIN_SUBAGENTS["fact-check-reviewer"]
    assert "task" in config.disallowed_tools
    assert "ask_clarification" in config.disallowed_tools
    assert "present_files" in config.disallowed_tools


def test_reviewer_has_review_protocol_in_prompt():
    """Verify the system prompt contains review protocol instructions."""
    from src.subagents.builtins import BUILTIN_SUBAGENTS

    config = BUILTIN_SUBAGENTS["fact-check-reviewer"]
    assert "review_protocol" in config.system_prompt
    assert "get_sourced_data" in config.system_prompt
    assert "fact_check" in config.system_prompt
    assert "web_search" in config.system_prompt


def test_reviewer_is_valid_subagent_config():
    """Verify it's a proper SubagentConfig instance."""
    from src.subagents.builtins import BUILTIN_SUBAGENTS
    from src.subagents.config import SubagentConfig

    config = BUILTIN_SUBAGENTS["fact-check-reviewer"]
    assert isinstance(config, SubagentConfig)
