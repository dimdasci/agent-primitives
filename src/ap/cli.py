"""Entry point for the ap2 CLI application.

This module provides a command-line interface for interacting with the
agent-based task processing system. It handles task input, execution,
and result display.
"""

import logging
from pathlib import Path

from anyio import run
from dotenv import load_dotenv
from langfuse import get_client
from openai import AsyncOpenAI
import typer

from src.ap.actions import Actions, Done
from src.ap.agent import go
from src.ap.config import Config
from src.ap.context import Context
from src.ap.either import Either
from src.ap.inmemory import ThreadInMemoryStore
from src.ap.thread import Thread

# Configure logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "ap.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize state store
thread_store = ThreadInMemoryStore()


def process(
    task: str,
    driver: str = typer.Option(
        "openai",
        "--driver",
        "-d",
        help="LLM driver to use (openai, anthropic, ollama, etc.)",
    ),
) -> int:
    """Process a task using the agent-based system."""
    # Set the active driver in configuration
    try:
        Config.set_driver(driver)
    except ValueError as e:
        typer.echo(f"Error: {e}")
        available_drivers = Config.get_available_drivers()
        typer.echo(f"Available drivers: {', '.join(available_drivers)}")
        return 1

    # Initialize context with all dependencies
    context = Context(
        client=AsyncOpenAI(),
        logger=logger,
        langfuse=get_client(),
        cli=typer,
        state=thread_store,
        driver=driver,
    )

    # Create and store a new thread for this task
    thread = Thread(query=task)
    thread_store.add(thread)

    typer.echo(f"Processing task: {task}")
    typer.echo(f"Thread ID: {thread.id}")

    # Run the agent loop and handle the result
    result = run(go, context, thread.id, backend="asyncio")
    logger.debug(f"Agent loop result: {result}")

    return _handle_result(result, thread)


def _handle_result(result: Either[Actions, str], thread: Thread) -> int:
    """Handle the result from the agent processing.

    Args:
        result: Either a successful action (Right) or an error message (Left)
        thread: The thread containing the processing history

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Use fold to handle the Either result more functionally
    fold_result: int = result.fold(
        on_left=lambda error: _handle_error(error),
        on_right=lambda action: _handle_success(action, thread),
    )
    return fold_result


def _handle_error(error: str) -> int:
    """Handle an error result.

    Args:
        error: The error message

    Returns:
        Exit code (always 1 for errors)
    """
    typer.echo(f"Error: {error}")
    logger.error(f"Error in processing: {error}")
    return 1


def _handle_success(action: Actions, thread: Thread) -> int:
    """Handle a successful result.

    Args:
        action: The successful action
        thread: The thread containing the processing history

    Returns:
        Exit code (always 0 for success)
    """
    if isinstance(action, Done):
        typer.echo(action.output)
        typer.echo("-" * 40)
    logger.info(f"Success: {action}")
    return 0


if __name__ == "__main__":
    load_dotenv()
    # Initialize Config to load the configuration file
    Config()
    typer.run(process)
