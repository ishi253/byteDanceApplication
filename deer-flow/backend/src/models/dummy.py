from __future__ import annotations

from typing import Any

from langchain.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult

"""Dummy chat model for dev builds.

This model never calls an external API. It returns a simple, deterministic
response that mimics an LLM so the rest of the LangGraph stack (streaming,
tools, UI) can be exercised without consuming credits.
"""



class DummyChatModel(BaseChatModel):
    """Local, no-network chat model for development."""

    model_name: str = "dummy-dev"

    @property
    def _llm_type(self) -> str:  # noqa: D401
        """Return identifier for this dummy model."""
        return "dummy-dev"

    def _build_response(self, messages: list[BaseMessage]) -> ChatResult:
        """Core implementation shared by sync and async generate."""
        last_human: HumanMessage | None = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_human = msg
                break

        user_text = ""
        if last_human is not None:
            content = last_human.content
            if isinstance(content, list):
                parts: list[str] = []
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        parts.append(str(part["text"]))
                user_text = " ".join(parts)
            else:
                user_text = str(content)

        base = (
            "This is a dummy dev response from DummyChatModel. "
            "No external LLM was called."
        )
        if user_text:
            base += f"\n\nYou wrote:\n{user_text}"

        ai_message = AIMessage(content=base)
        generation = ChatGeneration(message=ai_message)
        return ChatResult(generations=[generation])

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> ChatResult:
        """Synchronous generation hook."""
        return self._build_response(messages)

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> ChatResult:
        """Async generation hook used by streaming runtimes."""
        return self._build_response(messages)


