"""Factory for LLM drivers.

This module provides a factory for getting the appropriate LLM driver
function based on the configuration.
"""

from collections.abc import Awaitable, Callable

from src.ap import actions
from src.ap.config import Config
from src.ap.context import Context
from src.ap.drivers import anthropic, openai
from src.ap.either import Either
from src.ap.thread import Thread

# Type for step function in all drivers
StepFunction = Callable[[Context, Thread], Awaitable[Either[actions.Action, str]]]

# Registry of available drivers
# As more drivers are implemented, add them here
DRIVERS: dict[str, StepFunction] = {
    "openai": openai.step,
    "anthropic": anthropic.step,
    # Add more drivers as they are implemented:
    # "ollama": ollama.step,
    # "openai_langchain": openai_langchain.step,
}


def get_driver(driver_name: str | None = None) -> StepFunction:
    """Get the appropriate LLM driver function.

    Args:
        driver_name: The name of the driver to use, or None to use the active driver

    Returns:
        The step function for the specified driver

    Raises:
        ValueError: If the driver name is not registered
    """
    if driver_name is None:
        driver_name = Config.get_active_driver()

    if driver_name not in DRIVERS:
        raise ValueError(
            f"Unknown driver: {driver_name}. Available drivers: {list(DRIVERS.keys())}"
        )

    return DRIVERS[driver_name]
