"""Conversation thread management for actions in a task processing system."""

from textwrap import dedent
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from src.ap.either import Either, Left, Right


def generate_thread_id() -> str:
    """Generate a unique identifier for the thread."""
    return str(uuid4())[:6]


class Thread(BaseModel):
    """Represents a conversation thread for task processing."""

    id: str = Field(
        default_factory=generate_thread_id,
        description="Unique identifier for the thread.",
    )
    query: str = Field(..., description="User query for the thread.")
    actions: list[Any] = Field(
        default_factory=list, description="List of actions in the thread."
    )

    def add(self, action: Any) -> "Thread":
        """Add an action to the thread.

        Args:
            action: The action to add (instance of Action subclass)

        Returns:
            Self for method chaining
        """
        self.actions.append(action)
        return self

    def last(self) -> Either[Any, str]:
        """Get the last action in the thread.

        Returns:
            Either the last action (Right) or an error message (Left)
        """
        if self.actions:
            return Right(self.actions[-1])
        return Left("No actions in thread.")

    def __str__(self) -> str:
        return (
            dedent("""
            User query: {q}  
            Thread: [{t}]
        """)
            .format(q=self.query, t=", ".join(str(action) for action in self.actions))
            .strip()
        )
