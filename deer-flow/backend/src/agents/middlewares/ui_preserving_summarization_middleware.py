"""UI-preserving summarization middleware.

This middleware is the first concrete step toward a dual-history design:

- `messages` remain the full conversation history for the UI and checkpointer.
- `summary_history` (stored in `ThreadState.values`) holds a compact summary of
  earlier turns for future use in model prompts.

Important: in this iteration we **only compute and store the summary**. We do
*not* yet shorten the messages sent to the model, so behaviour remains safe and
backwards-compatible from the model's perspective while the UI gains access to
`summary_history`.
"""

from __future__ import annotations

from typing import Any, Iterable, override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.runtime import Runtime

from src.config.summarization_config import ContextSize, get_summarization_config
from src.models import create_chat_model


class UiSummarizationState(AgentState):
  """Compatible with the ThreadState schema.

  We rely on the existing fields:
  - messages: full conversation history
  - summary_history: optional string we will populate over time
  """

  pass


class UiPreservingSummarizationMiddleware(AgentMiddleware[UiSummarizationState]):
  """Scaffolding middleware for future UI-preserving summarization.

  Current behaviour:
  - Reads `messages` and `summary_history` but does not mutate either.
  - Does not call any LLMs yet.

  This ensures we can safely register it in the middleware chain without
  changing model prompts or UI-visible history. Follow-up iterations will add
  real summarization and prompt shaping logic.
  """

  state_schema = UiSummarizationState

  def __init__(self) -> None:  # noqa: D401
    """Initialize middleware using global summarization config."""
    super().__init__()
    self._config = get_summarization_config()

  # ---------------------------------------------------------------------------
  # Helpers
  # ---------------------------------------------------------------------------

  def _message_count(self, messages: list[BaseMessage]) -> int:
    return len(messages)

  def _should_summarize(self, messages: list[BaseMessage]) -> bool:
    """Decide whether to run summarization based on config."""
    cfg = self._config
    if not cfg.enabled or cfg.trigger is None:
      return False

    triggers: Iterable[ContextSize]
    if isinstance(cfg.trigger, list):
      triggers = cfg.trigger
    else:
      triggers = [cfg.trigger]

    count = self._message_count(messages)
    for t in triggers:
      if t.type == "messages" and count >= int(t.value):
        return True
      # Other trigger types (tokens, fraction) can be added later.
    return False

  def _split_history(
    self,
    messages: list[BaseMessage],
  ) -> tuple[list[BaseMessage], list[BaseMessage]]:
    """Split into (to_summarize, recent) based on keep policy."""
    cfg = self._config
    keep = cfg.keep
    if keep.type != "messages":
      # For now, treat non-message-based policies as "keep last N messages"
      # where N is value cast to int.
      keep_last = int(keep.value)
    else:
      keep_last = int(keep.value)

    if keep_last <= 0 or keep_last >= len(messages):
      return messages, []

    return messages[:-keep_last], messages[-keep_last:]

  def _format_history_for_summary(self, messages: list[BaseMessage]) -> str:
    """Render messages into a plain-text transcript for summarization."""
    lines: list[str] = []
    for msg in messages:
      role = "assistant"
      if isinstance(msg, HumanMessage):
        role = "user"
      elif isinstance(msg, SystemMessage):
        role = "system"
      elif isinstance(msg, AIMessage):
        role = "assistant"

      content = msg.content
      if isinstance(content, list):
        # LangChain content blocks – collect any text fields.
        parts: list[str] = []
        for part in content:
          if isinstance(part, dict) and "text" in part:
            parts.append(str(part["text"]))
        content = " ".join(parts)

      lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)

  def _summarize(self, transcript: str) -> str | None:
    """Call a lightweight chat model to summarize the transcript."""
    if not transcript.strip():
      return None

    cfg = self._config

    if cfg.model_name:
      model = create_chat_model(name=cfg.model_name, thinking_enabled=False)
    else:
      # Use default model in non-thinking mode; config can be tuned later to
      # pick a cheaper summarization-specific model.
      model = create_chat_model(thinking_enabled=False)

    system_prompt = cfg.summary_prompt or (
      "You are a helpful assistant that summarizes long conversations.\n"
      "Summarize the following chat history into a concise, factual overview "
      "that preserves key decisions, plans, and domain context. Do not invent "
      "new information.\n"
    )

    messages: list[BaseMessage] = [
      SystemMessage(content=system_prompt),
      HumanMessage(
        content=(
          "Here is the previous conversation history that may no longer fit in "
          "the model context window. Summarize it for future reference:\n\n"
          f"{transcript}"
        ),
      ),
    ]

    response = model.invoke(messages)
    content = getattr(response, "content", None)
    if not content:
      return None
    if isinstance(content, list):
      parts: list[str] = []
      for part in content:
        if isinstance(part, dict) and "text" in part:
          parts.append(str(part["text"]))
      return " ".join(parts).strip()
    return str(content).strip()

  @override
  def before_model(
    self,
    state: UiSummarizationState,
    runtime: Runtime,  # noqa: ARG002
  ) -> dict | None:
    """Currently a no-op.

    In future iterations this hook can build a reduced message list for the
    model based on `summary_history` + recent messages, while keeping the
    full `messages` history intact for the UI/checkpointer.
    """
    _ = state  # satisfy linters
    return None

  @override
  def after_agent(
    self,
    state: UiSummarizationState,
    runtime: Runtime,  # noqa: ARG002
  ) -> dict | None:
    """Compute and store a summary when thresholds are exceeded.

    This populates `summary_history` but does not modify `messages`.
    """
    cfg = self._config
    if not cfg.enabled:
      return None

    messages: list[BaseMessage] = state.get("messages") or []
    if not messages:
      return None

    if not self._should_summarize(messages):
      return None

    to_summarize, _recent = self._split_history(messages)
    if not to_summarize:
      return None

    transcript = self._format_history_for_summary(to_summarize)
    summary = self._summarize(transcript)
    if not summary:
      return None

    # Merge new summary with any existing one by appending; callers can choose
    # how to display this in the UI.
    existing: str | None = state.get("summary_history")  # type: ignore[assignment]
    if existing:
      combined = f"{existing}\n\n---\n\n{summary}"
    else:
      combined = summary

    return {"summary_history": combined}


