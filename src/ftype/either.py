from typing import Generic, TypeVar, Callable, Any

# Define generic types for success and error values
T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type


class Either(Generic[T, E]):
    """A generic Either type that can hold a value of type T (success) or E (error)."""

    ...


class Left(Either[Any, E]):
    """Represents a failure or error in the Either type."""

    def __init__(self, error: E):
        self.error = error

    def map(self, func: Callable[[T], T]) -> "Either[T, E]":
        return self  # Errors propagate unchanged

    def flat_map(self, func: Callable[[T], "Either[T, E]"]) -> "Either[T, E]":
        return self

    def fold(self, on_left: Callable[[E], Any], on_right: Callable[[T], Any]) -> Any:
        return on_left(self.error)


class Right(Either[T, Any]):
    """Represents a successful value in the Either type."""

    def __init__(self, value: T):
        self.value = value

    def map(self, func: Callable[[T], T]) -> "Either[T, E]":
        return Right(func(self.value))

    def flat_map(self, func: Callable[[T], "Either[T, E]"]) -> "Either[T, E]":
        return func(self.value)

    def fold(self, on_left: Callable[[E], Any], on_right: Callable[[T], Any]) -> Any:
        return on_right(self.value)
