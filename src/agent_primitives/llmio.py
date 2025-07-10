from .events import RequestInformation, Done, DoneWithError
from .tools import Add, Subtract, Multiply, Divide
from src.ftype import Either, Right, Left
from textwrap import dedent
from typing import Union
from tenacity import (retry, stop_after_attempt, wait_exponential, retry_if_exception_type)


Action = Union[RequestInformation, Done, DoneWithError, Add, Subtract, Multiply, Divide]


SYSTEM = dedent("""
    You are a helpful assistant that can help solve a given arithmetic
    task. 
                
    You break down the task into smaller steps, and use the tools
    provided to perform arithmetic operations. Never do calculations
    in your head, always use the tools to perform arithmetic operations.
                
    You do not need to confirm these operations with the user, 
    or confirm the plan. Go ahead when you know how to solve the task.
    
    You can request additional information from the user
    if you need more details to solve the task.
                
    When you're requested other types of tasks, gently refuse it and
    done with error.
    """)

PROMPT = dedent("""
    You are working on the following thread initiated by the user:
                
    <thread_history>
    {thread_history}
    </thread_history>
    
    What should the next step be? 
                
    Choose only one of the following actions:
    """)

@retry(
    stop=stop_after_attempt(1),
    wait=wait_exponential(multiplier=2, min=1, max=60)
)
def next_step(fn, context) -> Either[Action, str]:
    """
    Determines the next step in the agent's workflow based on
    the provided function and context.

    Args:
        fn: The function to execute for determining the next step.
        context: The context in which the function is executed.

    Returns:
        An instance of Action representing the next step.
    """

    prompt = PROMPT.format(thread_history=context.get("thread_history", "empty"))

    response = fn(
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        response_model=Action,
    )
    if isinstance(response, DoneWithError):
        return Left(
            response.text or "An unknown error occurred while processing the task."
        )

    return Right(response)
