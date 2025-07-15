from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast

# Define generic types for success and error values
T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type


class Either(Generic[T, E]):
    """A generic Either type that can hold a value of type T (success) or E (error).

    This class provides a way to handle computations that may fail,
    without using exceptions. It allows for functional-style error handling,
    where the error information is carried along with the computation result.
    """

    def map(self, func: Callable[[T], Any]) -> "Either[Any, E]":
        """Apply a function to the success value if this is a Right.

        Args:
            func: Function to apply to the success value

        Returns:
            A new Either with the function applied to the success value,
            or the original Left if this is a Left
        """
        if isinstance(self, Right):
            return cast(Right[T], self).map(func)
        else:
            return cast(Left[E], self)

    def flat_map(self, func: Callable[[T], "Either[Any, E]"]) -> "Either[Any, E]":
        """
        Apply a function that returns an Either to the success value if this is a Right.

        Args:
            func: Function that returns an Either

        Returns:
            The result of applying the function to the success value,
            or the original Left if this is a Left
        """
        if isinstance(self, Right):
            return cast(Right[T], self).flat_map(func)
        else:
            return cast(Left[E], self)

    def fold(self, on_left: Callable[[E], Any], on_right: Callable[[T], Any]) -> Any:
        """
        Apply one of two functions depending on whether this is a Left or Right.

        Args:
            on_left: Function to apply if this is a Left
            on_right: Function to apply if this is a Right

        Returns:
            The result of applying the appropriate function
        """
        if isinstance(self, Right):
            return cast(Right[T], self).fold(on_left, on_right)
        else:
            return cast(Left[E], self).fold(on_left, on_right)

    def is_right(self) -> bool:
        """Check if this Either is a Right.

        Returns:
            True if this is a Right, False otherwise
        """
        return isinstance(self, Right)

    def is_left(self) -> bool:
        """Check if this Either is a Left.

        Returns:
            True if this is a Left, False otherwise
        """
        return isinstance(self, Left)


class Left(Either[Any, E]):
    """Represents a failure or error in the Either type."""

    __match_args__ = ("error",)

    def __init__(self, error: E):
        self.error = error

    def __str__(self) -> str:
        return f"Left({self.error})"

    def map(self, func: Callable[[Any], Any]) -> "Either[Any, E]":
        return self  # Errors propagate unchanged

    def flat_map(self, func: Callable[[Any], "Either[Any, E]"]) -> "Either[Any, E]":
        return self  # Errors propagate unchanged

    def fold(self, on_left: Callable[[E], Any], on_right: Callable[[Any], Any]) -> Any:
        return on_left(self.error)


class Right(Either[T, Any]):
    """Represents a successful value in the Either type."""

    __match_args__ = ("value",)

    def __init__(self, value: T):
        self.value = value

    def __str__(self) -> str:
        return f"Right({self.value})"

    def map(self, func: Callable[[T], Any]) -> "Either[Any, Any]":
        return Right(func(self.value))

    def flat_map(self, func: Callable[[T], "Either[Any, Any]"]) -> "Either[Any, Any]":
        return func(self.value)

    def fold(self, on_left: Callable[[Any], Any], on_right: Callable[[T], Any]) -> Any:
        return on_right(self.value)
