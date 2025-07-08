import uuid  # For generating unique thread IDs
from src.agent_primitives.model import Thread
from logging import Logger
from threading import Lock


class ThreadInMemoryStore:
    """
    A class to represent a thread store.
    It contains a dictionary of threads indexed by their IDs.
    """

    threads: dict[str, Thread] = {}
    logger: Logger | None = None

    def __init__(self, logger: Logger | None = None) -> None:
        """
        Initialize the thread store with an optional logger.
        If a logger is provided, it will be used for logging operations.
        """
        self.lock = Lock()
        self.logger = logger
        if self.logger:
            self.logger.info("ThreadInMemoryStore initialized.")

    def add(self, thread: Thread) -> str:
        """
        Add a thread to the store and returns it id.
        """
        id = str(uuid.uuid4())[:6]

        with self.lock:
            self.threads[id] = thread

        if self.logger:
            self.logger.info(f"Thread added with ID: {id}")

        return id

    def get(self, thread_id: str) -> Thread | None:
        """
        Retrieve a thread by its ID.
        """

        if self.logger and thread_id not in self.threads:
            self.logger.warning(f"Thread with ID {thread_id} not found in store.")
        elif self.logger:
            self.logger.info(f"Retrieving thread with ID: {thread_id}")

        return self.threads.get(thread_id)

    def clear(self) -> None:
        """
        Clear all threads in the store.
        """
        if self.logger:
            self.logger.info("Clearing all threads in the store.")

        with self.lock:
            self.threads.clear()
