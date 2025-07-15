"""Agent module for handling actions in the application.

This module contains the core agent logic for processing tasks through
a sequence of actions. It implements a loop that repeatedly:
1. Determines the next action to take
2. Executes that action
3. Updates the thread history
4. Continues until a terminal action is reached
"""

from typing import cast

from src.ap import actions
from src.ap.actions import Actions
from src.ap.config import Config
from src.ap.context import Context
from src.ap.drivers import get_driver
from src.ap.either import Either, Left, Right
from src.ap.thread import Thread


async def go(ctx: Context, thread_id: str) -> Either[Actions, str]:
    """Process a task by retrieving the thread and running the agent loop.

    Args:
        ctx: Application context containing dependencies
        thread_id: Identifier of the thread to process

    Returns:
        Either a successful final action (Right) or an error message (Left)
    """
    thread_result = ctx.state.get(thread_id)

    # Use pattern matching but with simplified error handling
    match thread_result:
        case Left(error):
            ctx.logger.error(f"Failed to retrieve thread {thread_id}: {error}")
            return Left(error)
        case Right(thread):
            return await _process_thread(ctx, thread_id, thread)

    # This line will never be reached but helps the type checker
    return Left("Unreachable code - match should handle all cases")


async def _process_thread(
    ctx: Context, thread_id: str, thread: Thread
) -> Either[Actions, str]:
    """Process a thread after it has been successfully retrieved.

    Args:
        ctx: Application context containing dependencies
        thread_id: Identifier of the thread to process
        thread: The thread to process

    Returns:
        Either a successful final action (Right) or an error message (Left)
    """
    ctx.logger.info(f"Processing thread {thread_id}: {thread.query}")

    # Get the driver name for tagging
    driver_name = ctx.driver if hasattr(ctx, "driver") else "openai"

    with ctx.langfuse.start_as_current_span(
        name="agent-loop",
        input={"user_query": thread.query},
    ) as root_span:
        # Add trace metadata including the driver tag
        root_span.update_trace(
            session_id=thread_id,
            tags=[driver_name],
        )

        # Execute the agent loop
        result = await loop(ctx, thread)

        # Update the root span with the result
        if isinstance(result, Right):
            # If successful, include the action result
            action = result.value
            if isinstance(action, actions.Done):
                root_span.update(output={"result": str(action.output)})
            else:
                root_span.update(output={"result": str(action)})
        else:
            # If there was an error, include the error message
            assert isinstance(result, Left)
            root_span.update(output={"error": result.error})

        return result


async def loop(ctx: Context, thread: Thread) -> Either[Actions, str]:
    """Process a sequence of actions until completion or max iterations reached.

    Args:
        ctx: Application context with client, logger, etc.
        thread: Current thread containing the conversation history

    Returns:
        Either a successful final action (Right) or an error message (Left)

    The loop will continue processing actions until either:
    1. A Done action is encountered (success)
    2. An error occurs (Left return)
    3. Max iterations are reached (safety limit)
    """
    max_actions = Config.get("max_actions", 10)
    for iteration in range(max_actions):
        ctx.logger.debug(f"Starting iteration {iteration + 1}/{max_actions}")

        # Get the LLM driver based on the current context and get the next action
        step_function = get_driver(ctx.driver if hasattr(ctx, "driver") else None)
        action_result = await step_function(ctx, thread)

        if isinstance(action_result, Left):
            ctx.logger.error(f"Error determining next action: {action_result.error}")
            return action_result

        # Extract the action from the Right wrapper
        assert isinstance(action_result, Right)
        current_action = action_result.value

        # Ensure correct type for thread processing
        typed_action = cast(actions.Actions, current_action)

        try:
            # Execute the action
            execute_action(ctx, typed_action)
            ctx.cli.echo(f" - {typed_action}")
            ctx.logger.info(f"Executed action: {typed_action}")
        except Exception as e:
            error_msg = (
                f"Error executing action {typed_action.__class__.__name__}: {str(e)}"
            )
            ctx.logger.error(error_msg)
            return Left(error_msg)

        # Add the action to the thread history
        thread = thread.add(typed_action)
        ctx.logger.info(f"Added action to thread: {typed_action}")

        # Check if we've reached a terminal action
        if isinstance(typed_action, actions.Done):
            ctx.logger.info(f"Task completed with result: {typed_action}")
            return Right(typed_action)

    # If we get here, we've exceeded the maximum number of iterations
    error_msg = f"Exceeded maximum of {max_actions} actions without reaching completion"
    ctx.logger.warning(error_msg)
    return Left(error_msg)


def execute_action(ctx: Context, action: actions.Action) -> None:
    """Execute an action with the appropriate context.

    Args:
        ctx: Application context with dependencies
        action: The action to execute
    """
    # Different actions may need different kwargs
    kwargs = {}

    # Special handling for actions requiring IO
    if isinstance(action, actions.AskUser):
        kwargs["io"] = ctx.cli

    # Execute the action
    action.execute(**kwargs)
