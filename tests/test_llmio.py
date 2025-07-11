import pytest
import os
import logging
from functools import partial
from openai import OpenAI
import instructor
from dotenv import load_dotenv
from src.agent_primitives.llmio import next_step
from src.agent_primitives.events import RequestInformation, Done, DoneWithError
from src.ftype import Right, Left

# Configure logging for tests
logging.basicConfig(
    filename="log/test_instructor.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def log_completion_kwargs(*args, **kwargs) -> None:
    """
    Log the completion kwargs for debugging purposes.
    """
    logger.debug("Completion kwargs", extra=kwargs)


def log_completion_response(response) -> None:
    """
    Log the completion response for debugging purposes.
    """
    logger.debug("Completion response", extra={"response": response})


@pytest.fixture(scope="module")
def openai_client():
    """Fixture to set up the OpenAI client with instructor."""
    # Load environment variables
    load_dotenv()
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not set in environment variables")
    
    # Set up the OpenAI client with instructor
    client = instructor.from_openai(OpenAI())
    
    # Add hooks for logging
    client.on("completion:kwargs", log_completion_kwargs)
    client.on("completion:response", log_completion_response)
    
    return client


@pytest.mark.integration
def test_next_step_with_sample_history(openai_client):
    """
    Integration test for next_step with a sample thread history.
    This test verifies that the real OpenAI model responds as expected.
    """
    # Create a partial function with the client
    fn = partial(openai_client.chat.completions.create, model="gpt-4o-mini")
    
    # Sample context with thread history
    context = {
        "thread_history": '<step n="1"><user_input>This is a sample thread history for testing purposes.</user_input></step>'
    }
    
    # Call the function with real API
    result = next_step(fn, context)
    
    # Assert the expected outcome
    assert isinstance(result, Right), f"Expected Right but got {type(result)}"
    
    # We expect the model to ask for more information since our input is generic
    assert isinstance(result.value, RequestInformation), f"Expected RequestInformation but got {type(result.value)}"
    
    # Log the actual response for inspection
    logger.info(f"Model response: {result.value}")
    
    # The text should ask for arithmetic tasks since that's what our system prompt specifies
    assert result.value.text, "Response text should not be empty"
    assert result.value.chain_of_thought, "Chain of thought should not be empty"


@pytest.mark.integration
def test_next_step_with_arithmetic_query(openai_client):
    """
    Integration test for next_step with an arithmetic query.
    This test verifies that the agent uses tools correctly.
    """
    fn = partial(openai_client.chat.completions.create, model="gpt-4o-mini")
    
    # Thread history with an arithmetic task
    context = {
        "thread_history": '<step n="1"><user_input>What is 25 + 17?</user_input></step>'
    }
    
    # Call the function with real API
    result = next_step(fn, context)
    
    # Assert the expected outcome
    assert isinstance(result, Right), f"Expected Right but got {type(result)}: {result.error}" # type: ignore
    
    # Log the actual response for inspection
    logger.info(f"Model response for arithmetic query: {result.value}")
    
    # The model should either use the Add tool or provide a Done response
    # We can't assert exact behavior since the model response might vary
    assert hasattr(result.value, 'type'), "Response should have a type attribute"


@pytest.mark.integration
def test_next_step_with_non_arithmetic_query(openai_client):
    """
    Integration test for next_step with a non-arithmetic query.
    This tests the agent's ability to refuse non-arithmetic tasks as per the system prompt.
    """
    fn = partial(openai_client.chat.completions.create, model="gpt-4o-mini")
    
    # Thread history with a non-arithmetic task
    context = {
        "thread_history": '<step n="1"><user_input>Write me a poem about cats.</user_input></step>'
    }
    
    # Call the function with real API
    result = next_step(fn, context)
    
    # Assert the expected outcome
    assert isinstance(result, Right), f"Expected Right but got {type(result)}: {result.error}" # type: ignore
    
    # Log the actual response for inspection
    logger.info(f"Model response for non-arithmetic query: {result.value}")
    
    # The model should politely refuse or request arithmetic tasks instead
    assert hasattr(result.value, 'type'), "Response should have a type attribute"
    # We expect either RequestInformation or DoneWithError, but can't guarantee which one
