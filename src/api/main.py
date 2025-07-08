import logging
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.agent_primitives.agent import run as agent_run
from src.agent_primitives.model import Event, Thread, Intents
from src.agent_primitives.model import EventType as ET


# Configure logging
# set logging output to log/agent_primitives.log
logging.basicConfig(
    filename="log/agent_primitives_api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
# Create a logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Agent Primitives API",
    description="API for interacting with the Agent Primitives",
    version="0.1.0",
)


# Define request and response models
class MessageRequest(BaseModel):
    message: str


class ThreadResponse(BaseModel):
    thread_id: Optional[str] = None
    events: list[Dict[str, Any]]
    last_message: Optional[str] = None
    intent: Optional[str] = None


@app.post("/thread", response_model=ThreadResponse)
async def create_thread(request: MessageRequest):
    """
    Create a new thread with an initial user message and run the agent.
    """
    logger.info(f"Creating new thread with message: {request.message}")

    # Create a new thread with the user message
    thread = Thread(events=[Event(type=ET.USER_INPUT, data=request.message)])

    # Run the agent with the thread
    await agent_run(thread)

    # Get the last event
    last_event = thread.events[-1] if thread.events else None

    if not last_event:
        logger.error("No events found in the thread after agent run")
        raise HTTPException(status_code=500, detail="Agent processing failed")

    if last_event.type != ET.SYSTEM_RESPONSE:
        logger.error(f"Unexpected event type: {last_event.type}")
        raise HTTPException(
            status_code=500, detail=f"Unexpected event type: {last_event.type}"
        )

    # Format events for response
    events_data = []
    for event in thread.events:
        event_data = {"type": event.type.value, "data": event.data}
        if event.type == ET.SYSTEM_RESPONSE:
            event_data["intent"] = event.data.intent
            event_data["message"] = event.data.message
        events_data.append(event_data)

    # Return the response
    return ThreadResponse(
        events=events_data,
        last_message=last_event.data.message
        if last_event.type == ET.SYSTEM_RESPONSE
        else None,
        intent=last_event.data.intent
        if last_event.type == ET.SYSTEM_RESPONSE
        else None,
    )


@app.get("/thread/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str):
    """
    Get the status of a thread by ID.
    Note: This is a placeholder implementation.
    """
    # This would typically retrieve the thread from a database
    logger.info(f"Retrieving thread with ID: {thread_id}")
    raise HTTPException(status_code=404, detail="Not implemented yet")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
