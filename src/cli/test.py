from openai import OpenAI
import instructor
from dotenv import load_dotenv
from functools import partial
from src.agent_primitives.llmio import next_step
from src.ftype import Right, Left
import logging

# Configure logging
# set logging output to log/agent_primitives.log
logging.basicConfig(
    filename="log/test_instructor.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
# Create a logger
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


def main():
    # set up the OpenAI client
    client = instructor.from_openai(
        OpenAI(), 
        # mode=instructor.Mode.JSON
    )

    # add hooks to log requests and responses
    client.on("completion:kwargs", log_completion_kwargs)
    client.on("completion:response", log_completion_response)

    fn = partial(client.chat.completions.create, model="gpt-4o-mini")
    examples = [
        {
            "thread_history": '<step n="1"><user_input>What is 15 * (234 + 312) / 8?</user_input></step>'
        },
        {
            "thread_history": '<step n="1"><user_input>Can you help me with a math problem?</user_input></step>'
        },
        {
            "thread_history": '<step n="1"><user_input>What is the capital of France?</user_input></step>'
        },
    ]

    for context in examples:
        print (f"Processing context: {context['thread_history']}")
        try:
            result = next_step(fn, context)
        except Exception as e:
            logger.exception("An error occurred while determining the next action")
            result = Left(str(e))

        match result:
            case Right(action):
                print(f"Next action: {action}")
            case Left(error):
                print(f"Error determining next action: {error}")

        print("-" * 40)

if __name__ == "__main__":
    load_dotenv()
    main()
