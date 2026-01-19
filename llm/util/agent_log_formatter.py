"""
Log formatting utilities for agent step-by-step output in the Capstone project.

Responsibilities:
- Formats agent, tool, and user messages for readable logging and frontend streaming
- Truncates long arguments and responses for concise display
- Used by agent streaming and debugging flows
"""

from typing import Any


def format_log_event(event: dict[str, Any]) -> str:
    """
    Format a structured log event into a human-readable string.

    Args:
        event (dict): Event dictionary containing at least a 'type' key.
            Supported types: 'user', 'agent', 'tool_call', 'tool_result'.

    Returns:
        str: Formatted log message.
    """
    event_type = event.get("type")

    if event_type == "user":
        return "Receiving user input"

    if event_type == "agent":
        return "Final response from agent is on its way"

    if event_type == "tool_call":
        name = event.get("name", "Unknown Tool")
        args = truncate_args(str(event.get("args", "")))
        return f"Calling tool: {name} with arguments: {args}"

    if event_type == "tool_result":
        result = truncate_tool_response(str(event.get("result", "")))
        return f"Tool response received: {result}\nProcessing response, this may take a little while"

    return "Unknown event"


def truncate_args(args_str: str, limit: int = 200) -> str:
    """
    Truncate the arguments string to a specified character limit.
    Args:
        args_str (str): The arguments string.
        limit (int): Maximum number of characters to keep.
    Returns:
        str: Truncated arguments string.
    """
    truncated = args_str[:limit]
    return truncated + ("..." if len(args_str) > limit else "")


def truncate_tool_response(response_str: str, limit: int = 100) -> str:
    """
    Truncate the tool response string to a specified character limit.
    Args:
        response_str (str): The response string.
        limit (int): Maximum number of characters to keep.
    Returns:
        str: Truncated response string.
    """
    truncated = response_str[:limit]
    return truncated + ("..." if len(response_str) > limit else "")
