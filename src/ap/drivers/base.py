"""Base interfaces and protocols for LLM drivers.

This module defines the common interface that all LLM drivers must implement,
providing a consistent contract for the driver factory system.
"""

from collections.abc import Awaitable, Callable
from typing import Protocol

from src.ap import actions
from src.ap.context import Context
from src.ap.either import Either
from src.ap.thread import Thread


class LLMDriver(Protocol):
    """Protocol defining the interface for LLM drivers.

    All LLM drivers must implement this protocol to be compatible
    with the driver factory system.
    """

    async def step(self, ctx: Context, thread: Thread) -> Either[actions.Action, str]:
        """Determine the next action to execute based on the thread state.

        Args:
            ctx: Application context with client, logger, etc.
            thread: Current thread containing the query and action history

        Returns:
            Either an action to execute (Right) or an error message (Left)
        """
        ...


# Type alias for the step function that all drivers must provide
StepFunction = Callable[[Context, Thread], Awaitable[Either[actions.Action, str]]]
