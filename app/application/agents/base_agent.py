"""
Base agent abstract class.

All AI agents inherit from this. Defines the execution contract,
logging, timing, and error handling.
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.shared.logging.logger import get_logger

logger = get_logger(__name__)

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentResult(BaseModel):
    """Standard result wrapper for all agents."""

    success: bool
    agent_name: str
    duration_ms: int = 0
    tokens_used: int = 0
    error: str | None = None
    data: Any = None


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Abstract base class for all AI agents.

    Each agent has a single responsibility:
    - Typed input → Typed output
    - No side effects (no DB, no HTTP, no UI)
    - Independently testable
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._execution_id = str(uuid.uuid4())[:8]

    @property
    def name(self) -> str:
        return self._name

    async def run(self, input_data: InputT) -> AgentResult:
        """Execute the agent with timing and error handling."""
        start_time = time.monotonic()

        logger.info(
            "Agent started",
            agent=self._name,
            execution_id=self._execution_id,
        )

        try:
            output = await self.execute(input_data)
            duration_ms = int((time.monotonic() - start_time) * 1000)

            logger.info(
                "Agent completed",
                agent=self._name,
                execution_id=self._execution_id,
                duration_ms=duration_ms,
            )

            return AgentResult(
                success=True,
                agent_name=self._name,
                duration_ms=duration_ms,
                data=output.model_dump() if isinstance(output, BaseModel) else output,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(
                "Agent failed",
                agent=self._name,
                execution_id=self._execution_id,
                error=str(exc),
                duration_ms=duration_ms,
            )
            return AgentResult(
                success=False,
                agent_name=self._name,
                duration_ms=duration_ms,
                error=str(exc),
            )

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT:
        """
        Core agent logic — implemented by each concrete agent.

        Must:
        - Accept typed input
        - Return typed output
        - Raise on failure (caught by run())
        - Have no side effects
        """
        ...
