"""ThreadInMemoryStore class for managing threads in memory."""

from threading import Lock

from src.ap.either import Either, Left, Right
from src.ap.thread import Thread


class ThreadInMemoryStore:
    """
    A class to represent a thread store.

    It contains a dictionary of threads indexed by their IDs.
    """

    threads: dict[str, Thread] = {}

    def __init__(self) -> None:
        """
        Initialize the thread store with an optional logger.

        If a logger is provided, it will be used for logging operations.
        """
        self.lock = Lock()

    def add(self, thread: Thread) -> Thread:
        """Add a thread to the store and returns it id."""
        with self.lock:
            self.threads[thread.id] = thread

        return thread

    def get(self, thread_id: str) -> Either[Thread, str]:
        """Retrieve a thread by its ID."""
        if thread_id not in self.threads:
            return Left(f"Thread with ID {thread_id} not found in store.")

        return Right(self.threads[thread_id])

    def clear(self) -> "ThreadInMemoryStore":
        """Clear all threads in the store."""
        with self.lock:
            self.threads.clear()

        return self
