"""Anthropic LLM integration for determining next actions.

This module handles the communication with the Anthropic API to determine
the next action to take based on the current thread state.
"""

import json
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import Message, MessageParam

from src.ap import actions
from src.ap.config import Config
from src.ap.context import Context
from src.ap.either import Either, Left, Right
from src.ap.thread import Thread

# Load action information for the prompt
ACTIONS_FULL = actions.get_action_usage()
ACTIONS_SHORT = actions.get_action_names()

# Load examples for few-shot learning
EXAMPLES = Config.get_examples()


async def step(ctx: Context, thread: Thread) -> Either[actions.Action, str]:
    """Determine the next action to execute based on the thread state.

    Args:
        ctx: Application context with client, logger, etc.
        thread: Current thread containing the query and action history

    Returns:
        Either an action to execute (Right) or an error message (Left)
    """
    ctx.logger.info(f"Determining next action for thread: {thread.id} using Anthropic")

    # Get the system prompt
    system_prompt = get_system_prompt()

    # Prepare messages for the LLM
    messages = prepare_messages(system_prompt, thread)

    # Chain operations using flat_map
    completion_result = await get_completion(ctx, messages)
    return completion_result.flat_map(
        lambda completion: parse_completion(ctx, completion)
    ).flat_map(lambda response_object: convert_to_action(ctx, response_object))


def prepare_messages(system_prompt: str, thread: Thread) -> list[MessageParam]:
    """Prepare the messages for the Anthropic API.

    Args:
        system_prompt: The system prompt
        thread: The current thread with query and history

    Returns:
        List of messages for the LLM
    """
    return [{"role": "user", "content": str(thread)}]


async def get_completion(
    ctx: Context, messages: list[MessageParam]
) -> Either[Message, str]:
    """Get a completion from the Anthropic API.

    Args:
        ctx: Application context with logger
        messages: Messages to send to the LLM

    Returns:
        Either the completion message (Right) or an error message (Left)
    """
    try:
        # Use the client from the context or create a new one
        anthropic_client = AsyncAnthropic()

        model = Config.get("model")
        system = get_system_prompt()

        with ctx.langfuse.start_as_current_generation(
            name=__name__, model=model, input={"messages": messages, "system": system}
        ) as generation:
            completion = await anthropic_client.messages.create(
                model=model,
                max_tokens=Config.get("max_tokens", 1000),
                temperature=Config.get("temperature", 0.0),
                system=system,
                messages=messages,
            )
            generation.update(output=completion)

        return Right(completion)
    except Exception as e:
        return Left(f"Error getting completion from Anthropic: {str(e)}")


def parse_completion(ctx: Context, completion: Message) -> Either[dict[str, Any], str]:
    """Parse the completion response to a JSON object.

    Args:
        ctx: Application context with logger
        completion: The completion response from Anthropic

    Returns:
        Either the parsed JSON object (Right) or an error message (Left)
    """
    try:
        # Extract content from the message - Anthropic's content can be of
        # different types
        for content_block in completion.content:
            # We're looking for text blocks
            if content_block.type == "text":
                content = content_block.text
                if content:
                    try:
                        # Try to parse as JSON
                        json_obj = json.loads(content)
                        ctx.logger.info(f"Received action from Anthropic: {json_obj}")
                        return Right(json_obj)
                    except json.JSONDecodeError:
                        # If it's not valid JSON, try to extract JSON from the text
                        # Sometimes models wrap JSON in ```json blocks
                        import re

                        json_match = re.search(
                            r"```json\s*(.*?)\s*```", content, re.DOTALL
                        )
                        if json_match:
                            try:
                                json_obj = json.loads(json_match.group(1))
                                ctx.logger.info(
                                    f"Extracted JSON action from Anthropic: {json_obj}"
                                )
                                return Right(json_obj)
                            except json.JSONDecodeError:
                                pass

        # If we get here, we couldn't find valid JSON in any text block
        return Left("No valid JSON found in Anthropic response")
    except Exception as e:
        return Left(f"Error parsing output from Anthropic: {str(e)}")


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


def get_system_prompt() -> str:
    """Get the system prompt for the Anthropic model.

    Returns:
        The system prompt string
    """
    return f"""You are an AI assistant that helps users solve mathematical problems 
step by step.

AVAILABLE ACTIONS
{ACTIONS_FULL}

OUTPUT FORMAT
You must respond with a JSON object that contains an "action" field and an 
"arguments" field.
The "action" field must be one of: {ACTIONS_SHORT}.
The "arguments" field must be an object containing the arguments for the action.

EXAMPLES
{EXAMPLES}

Make sure your response can be parsed as valid JSON.
"""
