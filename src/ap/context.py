import logging
from typing import Protocol, runtime_checkable

from langfuse import Langfuse
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field

from src.ap.inmemory import ThreadInMemoryStore


@runtime_checkable
class UserPrompt(Protocol):
    """Protocol for user prompt interface."""

    def prompt(self, text: str) -> str:
        """Prompt the user for input."""
        ...

    def echo(self, message: str) -> None:
        """Echo text to the user."""
        ...


class Context(BaseModel):
    """Context for the application."""

    client: AsyncOpenAI = Field(default_factory=AsyncOpenAI)
    logger: logging.Logger = Field(default_factory=lambda: logging.getLogger(__name__))
    langfuse: Langfuse = Field(default_factory=Langfuse)
    cli: UserPrompt
    state: ThreadInMemoryStore = Field(default_factory=ThreadInMemoryStore)
    driver: str = Field(default="openai", description="The LLM driver to use")

    # Modern Pydantic V2 configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",  # no other fields are allowed to be set
    )
