import logging

from dotenv import load_dotenv
import typer
from anyio import run

from src.agent_primitives.agent import run as agent_run
from src.agent_primitives.model import Event, Thread, Intents
from src.agent_primitives.model import EventType as ET

# Configure logging
# set logging output to log/agent_primitives.log
logging.basicConfig(
    filename="log/agent_primitives.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
# Create a logger
logger = logging.getLogger(__name__)


def main():
    """Main function to run the agent CLI."""
    question = typer.prompt("What's your question?")
    logger.info(f"Running agent with question: {question}")

    message = run(agent_loop, question, backend="asyncio")
    typer.echo(message)
    logger.info(f"Agent response: {message}")


async def agent_loop(question: str) -> str:
    """Run the agent in a loop until the user decides to stop."""
    thread = Thread(events=[Event(type=ET.USER_INPUT, data=question)])
    while True:
        _ = await agent_run(thread)

        last_event = thread.events[-1] if thread.events else None
        if not last_event:
            logger.error("No events found in the thread.")
            typer.echo("No events found in the thread.")
            return "No response from agent."

        if last_event.type != ET.SYSTEM_RESPONSE:
            logger.error(f"Unexpected event type: {last_event.type}")
            typer.echo(f"Unexpected event type: {last_event.type}")
            return "Unexpected event type encountered."

        if Intents(last_event.data.intent) == Intents.DONE:
            return last_event.data.message
        elif Intents(last_event.data.intent) == Intents.REQUEST_INFO:
            question = typer.prompt(f"{last_event.data.message}? (type 'exit' to quit)")
            if question.lower() == "exit":
                return "Exiting agent loop."
            thread.events.append(Event(type=ET.USER_INPUT, data=question))
        else:
            logger.warning(f"Unhandled intent: {last_event.data.intent}")
            typer.echo(f"Unhandled intent: {last_event.data.intent}")
            return "Unhandled intent encountered."


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    typer.echo("Welcome to the Agent Primitives CLI!")
    typer.run(main)
