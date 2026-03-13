"""Middleware that auto-discovers output files and adds them to artifacts.

After each agent invocation, scans the thread's outputs directory for files
that are not yet tracked in ``ThreadState.artifacts`` and adds them.  This
ensures intermediate files (data summaries, analysis frameworks, etc.) appear
in the UI even when the agent does not explicitly call ``present_files``.
"""

import logging
from pathlib import Path
from typing import NotRequired, override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langgraph.runtime import Runtime

from src.agents.thread_state import ThreadDataState
from src.config.paths import VIRTUAL_PATH_PREFIX

logger = logging.getLogger(__name__)

OUTPUTS_VIRTUAL_PREFIX = f"{VIRTUAL_PATH_PREFIX}/outputs"


class ArtifactDiscoveryState(AgentState):
    """Compatible with the ``ThreadState`` schema."""

    artifacts: list[str]
    thread_data: NotRequired[ThreadDataState | None]


class ArtifactDiscoveryMiddleware(AgentMiddleware[ArtifactDiscoveryState]):
    """Scan the outputs directory after each agent run and surface new files as artifacts."""

    state_schema = ArtifactDiscoveryState

    @override
    def after_agent(self, state: ArtifactDiscoveryState, runtime: Runtime) -> dict | None:
        thread_data = state.get("thread_data")
        if thread_data is None:
            return None

        outputs_path = thread_data.get("outputs_path")
        if not outputs_path:
            return None

        outputs_dir = Path(outputs_path)
        if not outputs_dir.is_dir():
            return None

        existing_artifacts: set[str] = set(state.get("artifacts") or [])

        discovered: list[str] = []
        for file_path in sorted(outputs_dir.rglob("*")):
            if not file_path.is_file():
                continue
            relative = file_path.relative_to(outputs_dir).as_posix()
            virtual_path = f"{OUTPUTS_VIRTUAL_PREFIX}/{relative}"
            if virtual_path not in existing_artifacts:
                discovered.append(virtual_path)

        if not discovered:
            return None

        logger.info("ArtifactDiscovery: found %d new file(s): %s", len(discovered), discovered)
        return {"artifacts": discovered}
