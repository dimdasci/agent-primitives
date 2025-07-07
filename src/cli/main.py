import typer
from src.agent_primitives.agent import run
from dotenv import load_dotenv
import logging

# Configure logging
# set logging output to log/agent_primitives.log
logging.basicConfig(
    filename='log/agent_primitives.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Create a logger
logger = logging.getLogger(__name__)

def main(question: str):
    typer.echo("Here is the answer:")
    typer.echo(run(question))

if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    typer.echo("Welcome to the Agent Primitives CLI!")
    typer.run(main)