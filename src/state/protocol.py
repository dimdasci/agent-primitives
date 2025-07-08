from typing import Protocol
from src.agent_primitives.model import Thread


class ThreadStore(Protocol):
    """
    A protocol for memory management in the agent system.
    This protocol defines methods for adding, retrieving, and clearing memory.
    """

    def add(self, thread: Thread) -> str:
        """
        Add a thread to the memory. Returns the thread ID.
        """
        ...

    def get(self, key: str) -> Thread | None:
        """
        Retrieve a thread from the memory by its key.
        """
        ...

    def clear(self) -> None:
        """
        Clear all entries in the memory.
        """
        ...
