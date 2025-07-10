from pydantic import BaseModel, Field
from typing import Literal

class Add(BaseModel):
    """Repesents an addition operation."""

    type: Literal["Add"]
    a: int | float = Field(..., description="The first number to add.")
    b: int | float = Field(..., description="The second number to add.")

    def result(self) -> int | float:
        """Returns the result of the addition."""
        return self.a + self.b

    def __str__(self) -> str:
        return f'<add a="{self.a}", b="{self.b}"/>'


class Subtract(BaseModel):
    """Represents a subtraction operation."""

    type: Literal["Subtract"]
    a: int | float = Field(..., description="The number to subtract from.")
    b: int | float = Field(..., description="The number to subtract.")

    def result(self) -> int | float:
        """Returns the result of the subtraction."""
        return self.a - self.b

    def __str__(self) -> str:
        return f'<subtract a="{self.a}", b="{self.b}"/>'


class Multiply(BaseModel):
    """Represents a multiplication operation."""

    type: Literal["Multiply"]
    a: int | float = Field(..., description="The first number to multiply.")
    b: int | float = Field(..., description="The second number to multiply.")

    def result(self) -> int | float:
        """Returns the result of the multiplication."""
        return self.a * self.b

    def __str__(self) -> str:
        return f'<multiply a="{self.a}", b="{self.b}"/>'


class Divide(BaseModel):
    """Represents a division operation."""

    type: Literal["Divide"]
    a: int | float = Field(..., description="The numerator.")
    b: int | float = Field(..., description="The denominator.")

    def result(self) -> float:
        """Returns the result of the division."""
        if self.b == 0:
            raise ValueError(f"Division by zero is not allowed: {self.a} / {self.b}.")
        return self.a / self.b

    def __str__(self) -> str:
        return f'<divide a="{self.a}", b="{self.b}"/>'
