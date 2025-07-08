from enum import Enum
from typing import Any

from pydantic import BaseModel


class Intents(Enum):
    """Enum to represent the intentions of the agent."""

    REQUEST_INFO = "request_more_information"
    DONE = "done_for_now"
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"


class EventType(Enum):
    """Enum to represent the type of events in the agent system."""

    USER_INPUT = "user_input"
    SYSTEM_RESPONSE = "system_response"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    ERROR = "error"


class Event(BaseModel):
    """Base class for events in the agent system."""

    type: EventType
    data: Any


class Thread(BaseModel):
    """Class to represent a thread of conversation or interaction."""

    events: list[Event]

    def serialize(self) -> str:
        """Serialize the thread to a string format."""
        return "\n".join(event.model_dump_json() for event in self.events)
