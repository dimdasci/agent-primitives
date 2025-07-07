from src.baml_client.sync_client import b
from src.baml_client.types import DoneForNow

def run(question: str) -> str:
    """
    Run the agent with the given question.
    """
    d: DoneForNow = b.DetermineNextStep(question)
    return d.message