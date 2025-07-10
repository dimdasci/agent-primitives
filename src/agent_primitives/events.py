from pydantic import BaseModel, Field
from typing_extensions import Literal

class UserInput(BaseModel):
    """
    Represents user input for an event.
    """

    type: Literal["UserInput"]
    text: str = Field(..., description="The text input from the user.")

    def __str__(self) -> str:
        return f"<user_input>{self.text}</user_input>"


class RequestInformation(BaseModel):
    """
    Represents agent request for additional information.
    """

    type: Literal["RequestInformation"]
    chain_of_thought: str = Field(
        ..., description="The chain of thought leading to the request for information."
    )
    text: str = Field(
        ..., description="An explanation of the information needed by the agent."
    )

    def __str__(self) -> str:
        return f"<request_information><chain_of_thought>{self.chain_of_thought}</chain_of_thought><text>{self.text}</text></request_information>"


class ToolResult(BaseModel):
    """
    Represents the result of a tool operation.
    """

    type: Literal["ToolResult"]
    tool_name: str = Field(
        ..., description="The name of the tool used to perform the operation."
    )
    result: str = Field(..., description="The result of the tool operation.")

    def __str__(self) -> str:
        return f'<tool_result name="{self.tool_name}">{self.result}</tool_result>'


class Done(BaseModel):
    """
    Represents the completion of an agent's task.
    """

    type: Literal["Done"]
    chain_of_thought: str = Field(
        ..., description="The chain of thought leading to the task completion."
    )
    text: str = Field(
        ...,
        description="The final agent response containing the output or result of the task",
    )

    def __str__(self) -> str:
        return f"<done><chain_of_thought>{self.chain_of_thought}</chain_of_thought><text>{self.text}</text></done>"


class DoneWithError(BaseModel):
    """Represents an error that occurred during the agent's task and halts it."""

    type: Literal["DoneWithError"]
    chain_of_thought: str = Field(
        ..., description="The chain of thought leading to the error."
    )
    text: str = Field(..., description="An explanation of the error that occurred.")

    def __str__(self) -> str:
        return f"<done_with_error><chain_of_thought>{self.chain_of_thought}</chain_of_thought><text>{self.text}</text></done_with_error>"
