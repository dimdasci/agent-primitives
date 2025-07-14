"""Ollama LLM integration for determining next actions.

This module handles the communication with the Ollama API to determine
the next action to take based on the current thread state.
"""

import json
from typing import Any

import ollama

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
    ctx.logger.info(f"Determining next action for thread: {thread.id} using Ollama")

    # Get the prompts for the LLM
    system_prompt, user_prompt = get_prompts(thread)

    # Prepare messages for the LLM
    messages = prepare_messages(system_prompt, user_prompt)

    # Chain operations using flat_map
    completion_result = await get_completion(ctx, messages)
    return completion_result.flat_map(
        lambda completion: parse_completion(ctx, completion)
    ).flat_map(lambda response_object: convert_to_action(ctx, response_object))


def prepare_messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    """Prepare the messages for the Ollama API.

    Args:
        system_prompt: The system prompt
        user_prompt: The user prompt

    Returns:
        List of messages for the LLM
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


async def get_completion(
    ctx: Context, messages: list[dict[str, str]]
) -> Either[Any, str]:
    """Get a completion from the Ollama API.

    Args:
        ctx: Application context with logger
        messages: Messages to send to the LLM

    Returns:
        Either the completion response (Right) or an error message (Left)
    """
    try:
        model = Config.get("model")
        
        with ctx.langfuse.start_as_current_generation(
            name=__name__, model=model, input={"messages": messages}
        ) as generation:
            # Use the async client from ollama
            client = ollama.AsyncClient()
            
            completion = await client.chat(
                model=model,
                messages=messages,
                options={
                    "temperature": Config.get("temperature", 0.0),
                    "num_predict": Config.get("max_tokens", 1000),
                },
                format="json",  # Request JSON format
            )
            
            # Extract token usage from ollama response
            usage_details = {}
            if (hasattr(completion, 'prompt_eval_count') and 
                completion.prompt_eval_count):
                usage_details["input"] = completion.prompt_eval_count
            if hasattr(completion, 'eval_count') and completion.eval_count:
                usage_details["output"] = completion.eval_count
            
            # Update generation with response and usage
            generation.update(output=completion, usage_details=usage_details)

        return Right(completion)
    except Exception as e:
        return Left(f"Error getting completion from Ollama: {str(e)}")


def parse_completion(
    ctx: Context, completion: Any
) -> Either[dict[str, Any], str]:
    """Parse the completion response to a JSON object.

    Args:
        ctx: Application context with logger
        completion: The completion response from Ollama

    Returns:
        Either the parsed JSON object (Right) or an error message (Left)
    """
    try:
        # Extract content from the message
        content = completion.get("message", {}).get("content", "")
        if not content:
            return Left("No content in Ollama response")

        try:
            # Try to parse as JSON
            json_obj = json.loads(content)
            ctx.logger.info(f"Received action from Ollama: {json_obj}")
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
                        f"Extracted JSON action from Ollama: {json_obj}"
                    )
                    return Right(json_obj)
                except json.JSONDecodeError:
                    pass

        # If we get here, we couldn't find valid JSON
        return Left(f"No valid JSON found in Ollama response: {content}")
    except Exception as e:
        return Left(f"Error parsing output from Ollama: {str(e)}")


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
    """Get the system and user prompts for Ollama.

    Args:
        thread: The current thread with query and history

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    examples = Config.get_prompt("ollama", "examples")
    system_prompt = Config.get_prompt("ollama", "system")
    user_prompt = Config.get_prompt(
        "ollama", "user",
        actions_full=ACTIONS_FULL,
        actions_short=ACTIONS_SHORT,
        examples=examples,
        query=thread.query,
        thread=str(thread),
    )
    return system_prompt, user_prompt