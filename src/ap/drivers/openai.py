"""OpenAI LLM integration for determining next actions.

This module handles the communication with the OpenAI API to determine
the next action to take based on the current thread state.
"""

import json
from typing import Any

from openai.types.chat import (
    ChatCompletionMessageParam,
)

from src.ap import actions
from src.ap.config import Config
from src.ap.context import Context
from src.ap.either import Either, Left, Right
from src.ap.thread import Thread

# Load action information for the prompt
ACTIONS_FULL = actions.get_action_usage()
ACTIONS_SHORT = actions.get_action_names()


async def step(ctx: Context, thread: Thread) -> Either[actions.Action, str]:
    """Determine the next action to execute based on the thread state.

    Args:
        ctx: Application context with client, logger, etc.
        thread: Current thread containing the query and action history

    Returns:
        Either an action to execute (Right) or an error message (Left)
    """
    ctx.logger.info(f"Determining next action for thread: {thread.id}")

    # Get the prompts for the LLM
    system_prompt, user_prompt = get_prompts(thread)

    # Prepare messages for the LLM
    messages = prepare_messages(system_prompt, user_prompt)

    # Chain operations using flat_map
    completion_result = await get_completion(ctx, messages)
    return completion_result.flat_map(
        lambda completion: parse_completion(ctx, completion)
    ).flat_map(lambda response_object: convert_to_action(ctx, response_object))


def prepare_messages(
    system_prompt: str, user_prompt: str
) -> list[ChatCompletionMessageParam]:
    """Prepare the messages for the LLM.

    Args:
        system_prompt: The system/developer prompt
        user_prompt: The user prompt

    Returns:
        List of messages for the LLM
    """
    return [
        {
            "role": "developer",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]


async def get_completion(
    ctx: Context, messages: list[ChatCompletionMessageParam]
) -> Either[Any, str]:
    """Get a completion from the OpenAI API.

    Args:
        ctx: Application context with client, logger, etc.
        messages: Messages to send to the LLM

    Returns:
        Either the completion object (Right) or an error message (Left)
    """
    try:
        model = Config.get("model")
        with ctx.langfuse.start_as_current_generation(
            name=__name__, model=model, input=messages
        ) as generation:
            completion = await ctx.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=Config.get("max_tokens", 1000),
                temperature=Config.get("temperature", 0.0),
                response_format={"type": Config.get("response_format", "json_object")},
            )
            generation.update(output=completion)

        # Check for issues with the completion and convert to Either
        if completion.choices[0].finish_reason != "stop":
            return Left(
                f"Unexpected finish reason: {completion.choices[0].finish_reason}"
            )

        if completion.choices[0].message.refusal:
            return Left(f"Refused: {completion.choices[0].message.refusal}")

        return Right(completion)
    except Exception as e:
        return Left(f"Error getting completion: {str(e)}")


def parse_completion(ctx: Context, completion: Any) -> Either[dict[str, Any], str]:
    """Parse the completion response to a JSON object.

    Args:
        ctx: Application context with logger
        completion: The completion response from OpenAI

    Returns:
        Either the parsed JSON object (Right) or an error message (Left)
    """
    try:
        # Check for content and parse in a more functional way
        content = completion.choices[0].message.content
        if not content:
            return Left("No content in completion message")

        json_obj = json.loads(content)
        ctx.logger.info(f"Received action: {json_obj}")
        return Right(json_obj)
    except Exception as e:
        return Left(f"Error parsing output: {str(e)}")


def convert_to_action(
    ctx: Context, json_obj: dict[str, Any]
) -> Either[actions.Action, str]:
    """Convert a JSON object to an Action instance.

    Args:
        ctx: Application context with logger
        json_obj: The parsed JSON object from the LLM

    Returns:
        Either an Action instance (Right) or an error message (Left)
    """
    try:
        action_class = actions.get_args(actions.Actions)
        action_name = json_obj.get("action")
        arguments = json_obj.get("arguments", {})

        # Find the matching class and create an instance
        matching_classes = [cls for cls in action_class if cls.__name__ == action_name]

        if not matching_classes:
            return Left(f"Unknown action type: {action_name}")

        action_instance = matching_classes[0](**arguments)
        ctx.logger.info(f"Converted to action class: {action_instance}")
        return Right(action_instance)
    except Exception as e:
        return Left(f"Error converting to action: {str(e)}")


def get_prompts(thread: Thread) -> tuple[str, str]:
    """Get the system and user prompts for OpenAI.

    Args:
        thread: The current thread with query and history

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    examples = Config.get_prompt("openai", "examples")
    system_prompt = Config.get_prompt(
        "openai", "system",
        actions_full=ACTIONS_FULL,
        actions_short=ACTIONS_SHORT,
        examples=examples,
    )
    user_prompt = Config.get_prompt(
        "openai", "user",
        query=thread.query,
        thread=str(thread),
    )
    return system_prompt, user_prompt
