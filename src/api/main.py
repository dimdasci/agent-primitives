import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path, Request
from pydantic import BaseModel

from src.agent_primitives.agent import run as agent_run
from src.agent_primitives.model import Event, Thread, Intents
from src.agent_primitives.model import EventType as ET
from src.state import ThreadInMemoryStore

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

# Initialize the in-memory store
store = ThreadInMemoryStore(logger=logger)


# Define request and response models
class MessageRequest(BaseModel):
    message: str


class ThreadResponse(BaseModel):
    thread_id: str
    thread: Thread
    message: str | None = None
    intent: Intents | None = None
    response_url: str | None


@app.post("/thread", response_model=ThreadResponse)
async def create_thread(request: MessageRequest, req: Request):
    """
    Create a new thread with an initial user message and run the agent.
    """
    logger.info(f"Creating new thread with message: {request.message}")

    # Create a new thread with the user message
    thread = Thread(events=[Event(type=ET.USER_INPUT, data=request.message)])

    # Store the thread in memory
    thread_id = store.add(thread)
    response_url = str(req.url_for("process_thread_response", thread_id=thread_id))

    return await pass_to_agent(thread_id, thread, response_url)


@app.get("/thread/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str = Path(..., regex="^[a-zA-Z0-9]{6}$")):
    """
    Get the status of a thread by ID.
    Note: This is a placeholder implementation.
    """

    logger.info(f"Retrieving thread with ID: {thread_id}")
    thread = store.get(thread_id)
    if thread is None:
        logger.error(f"Thread #{thread_id} not found")
        raise HTTPException(status_code=404, detail=f"Thread #{thread_id} not found")

    return ThreadResponse(
        thread_id=thread_id,
        thread=thread,
        message=None,
        intent=None,
        response_url=f"/thread/{thread_id}/response",
    )


@app.post("/thread/{thread_id}/response", response_model=ThreadResponse)
async def process_thread_response(
    request: MessageRequest,
    req: Request,
    thread_id: str = Path(..., regex="^[a-zA-Z0-9]{6}$"),
):
    """
    Process a response for a specific thread.
    """

    thread = store.get(thread_id)

    if thread is None:
        logger.error(f"Thread #{thread_id} not found")
        raise HTTPException(status_code=404, detail=f"Thread #{thread_id} not found")

    thread.events.append(Event(type=ET.USER_INPUT, data=request.message))
    request_url = str(req.url_for("process_thread_response", thread_id=thread_id))

    return await pass_to_agent(thread_id, thread, request_url)


async def pass_to_agent(id: str, thread: Thread, response_url: str) -> ThreadResponse:
    """
    Pass the thread to the agent for processing.
    """
    logger.info(f"Passing thread {id} to agent for processing.")

    # Run the agent with the thread
    try:
        await agent_run(thread)
    except Exception as e:
        logger.error(f"Error running agent for thread {id}: {e}")
        raise HTTPException(status_code=500, detail="Agent processing failed")

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

    # Return the response
    return ThreadResponse(
        thread_id=id,
        thread=thread,
        message=last_event.data.message if last_event.data else None,
        intent=last_event.data.intent if last_event.data else None,
        response_url=response_url,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
