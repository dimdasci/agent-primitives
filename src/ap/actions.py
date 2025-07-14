"""This module defines various actions that can be executed within a context."""

from typing import Any, get_args

from pydantic import BaseModel, Field

Result = Any | None


class Action(BaseModel):
    chain_of_thought: str = Field(
        default="", description="Step-by-step reasoning that led to this action choice."
    )
    r: Result | None = Field(
        default=None, description="Result of the action execution.", exclude=True
    )

    @property
    def result(self) -> Result:
        """Get the result of the action execution."""
        return self.r if self.r is not None else "Not yet calculated"

    def _compute_result(self, **kwargs: Any) -> Result:
        """
        Define how to compute the result for this action.

        This method should be overridden by subclasses to implement specific action
        logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def execute(self, **kwargs: Any) -> Result:
        """
        Execute the action with the provided context.

        This method ensures the action is executed only once, and subsequent
        calls return the cached result.
        """
        if self.r is None:
            self.r = self._compute_result(**kwargs)
        return self.r


class Add(Action):
    a: float = Field(..., description="First operand.")
    b: float = Field(..., description="Second operand.")

    def _compute_result(self, **kwargs: Any) -> Result:
        return self.a + self.b

    def __str__(self) -> str:
        return f"Add(a={self.a}, b={self.b}), result={self.result})"

    @classmethod
    def usage(cls) -> str:
        return f"{cls.__name__}(a: number, b: number): Add two numbers (a + b)."


class Subtract(Action):
    a: float = Field(..., description="Minuend.")
    b: float = Field(..., description="Subtrahend.")

    def _compute_result(self, **kwargs: Any) -> Result:
        return self.a - self.b

    def __str__(self) -> str:
        return f"Subtract(a={self.a}, b={self.b}), result={self.result})"

    @classmethod
    def usage(cls) -> str:
        return f"{cls.__name__}(a: number, b: number): Subtract two numbers (a - b)."


class Multiply(Action):
    a: float = Field(..., description="First operand.")
    b: float = Field(..., description="Second operand.")

    def _compute_result(self, **kwargs: Any) -> Result:
        return self.a * self.b

    def __str__(self) -> str:
        return f"Multiply(a={self.a}, b={self.b}), result={self.result})"

    @classmethod
    def usage(cls) -> str:
        return f"{cls.__name__}(a: number, b: number): Multiply two numbers (a * b)."


class Divide(Action):
    a: float = Field(..., description="Dividend.")
    b: float = Field(..., description="Divisor.")

    def _compute_result(self, **kwargs: Any) -> Result:
        if self.b == 0:
            raise ValueError("Division by zero is not allowed.")
        return self.a / self.b

    def __str__(self) -> str:
        return f"Divide(a={self.a}, b={self.b}), result={self.result})"

    @classmethod
    def usage(cls) -> str:
        return f"{cls.__name__}(a: number, b: number): Divide two numbers (a / b)."


class AskUser(Action):
    request: str = Field(..., description="Request for user input.")

    def _compute_result(self, **kwargs: Any) -> Result:
        """Returns user input for the request."""
        if "io" not in kwargs:
            raise ValueError("IO object must be provided to execute AskUser action")
        return kwargs["io"].prompt(self.request)

    def __str__(self) -> str:
        return f"RequestUserInput(request={self.request}), result={self.result})"

    @classmethod
    def usage(cls) -> str:
        return (
            f"{cls.__name__}(request: str): Request user input with a specific message."
        )


class Done(Action):
    output: float | str | None = Field(None, description="Final result of the actions.")

    def _compute_result(self, **kwargs: Any) -> Result:
        return self.output

    def __str__(self) -> str:
        return f"Done(output={self.output})"

    @classmethod
    def usage(cls) -> str:
        return (
            f"{cls.__name__}(output: str | number): Mark the task as done "
            f"with a result."
        )


# Helper functions to get action classes and their usage
Actions = Add | Subtract | Multiply | Divide | AskUser | Done

_ACTION_CLASSES = get_args(Actions)


def get_action_usage() -> str:
    """Generate usage documentation for all actions."""
    usage_docs = [
        "- " + action.usage() for action in _ACTION_CLASSES if hasattr(action, "usage")
    ]
    return "\n".join(usage_docs)


def get_action_names() -> str:
    """Get a comma-separated list of action names."""
    return ", ".join(action.__name__ for action in _ACTION_CLASSES)
