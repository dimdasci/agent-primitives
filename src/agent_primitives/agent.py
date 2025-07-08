from src.agent_primitives.model import Event, Intents, Thread
from src.agent_primitives.model import EventType as et
from src.baml_client.async_client import b

ACTIONS = {
    Intents.ADD: lambda x, y: x + y,
    Intents.SUBTRACT: lambda x, y: x - y,
    Intents.MULTIPLY: lambda x, y: x * y,
    Intents.DIVIDE: lambda x, y: x / y,
}


async def run(thread: Thread) -> Thread:
    """Run the agent with the given question."""
    while True:
        # Call the BAML function to determine the next step
        next_step = await b.DetermineNextStep(thread=thread.serialize())

        # Define intent
        intent = Intents(next_step.intent)
        if intent in (Intents.DONE, Intents.REQUEST_INFO):
            thread.events.append(Event(type=et.SYSTEM_RESPONSE, data=next_step))  # type: ignore
            return thread
        elif intent in (
            Intents.ADD,
            Intents.SUBTRACT,
            Intents.MULTIPLY,
            Intents.DIVIDE,
        ):
            thread.events.append(Event(type=et.TOOL_CALL, data=next_step))
            try:
                result = ACTIONS[intent](next_step.a, next_step.b)  # type: ignore
                result_type = et.TOOL_RESPONSE
            except Exception as e:
                result = str(e)
                result_type = et.ERROR
            thread.events.append(Event(type=result_type, data=result))
        else:
            raise ValueError(f"Unknown intent: {intent}")
