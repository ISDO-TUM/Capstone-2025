"""
Log formatting utilities for agent step-by-step output in the Capstone project.

Responsibilities:
- Formats agent, tool, and user messages for readable logging and frontend streaming
- Extracts tool names, arguments, and responses from log messages
- Truncates long arguments and responses for concise display
- Used by agent streaming and debugging flows
"""

import re


def format_log_message(message):
    """
    Format log messages based on their type (user, agent, tool).
    Args:
        message (str): The raw log message.
    Returns:
        str: Formatted, human-readable log message.
    """
    # Format log messages based on type
    if "Human Message" in message:
        return "Receiving user input"
    elif "Ai Message" in message:
        if "Tool Calls:" in message:
            # Extract tool name and arguments
            tool_name = extract_tool_name(message)
            args = extract_args(message)
            return f"Calling tool: {tool_name} with arguments: {args}"
        else:
            return "Final response from agent is on its way"
    elif "Tool Message" in message:
        response = extract_tool_response(message)
        return f"Tool response received: {response}\n Processing response, this may take a little while"

    return message


def extract_tool_name(message):
    """
    Extract the tool name from a log message.
    Args:
        message (str): The log message.
    Returns:
        str: The extracted tool name, or 'Unknown Tool' if not found.
    """
    # Look for patterns like "Tool Call: tool_name"
    match = re.search(r"Tool Calls?:\s*(\w+)", message)
    if match:
        return match.group(1)
    else:
        match = re.search(r"Name:\s*(\w+)", message)
    return "Unknown Tool"


def extract_args(message):
    """
    Extract and truncate the arguments from a log message.
    Args:
        message (str): The log message.
    Returns:
        str: Truncated arguments string, or a default message if not found.
    """
    # Search for the "Args" part of the log message
    match = re.search(r"Args:\s*(.*)", message)
    if match:
        args = match.group(1)
        # Truncate the arguments if necessary (e.g., limit to first 5 items)
        truncated_args = truncate_args(args)
        return truncated_args
    return "No arguments found"


def truncate_args(args_str, limit=200):
    """
    Truncate the arguments string to a specified character limit.
    Args:
        args_str (str): The arguments string.
        limit (int): Maximum number of characters to keep.
    Returns:
        str: Truncated arguments string.
    """
    # Truncate arguments list to the first 'limit' items
    try:
        # Parse the string into a list
        truncated = args_str[:limit]
        # Return the truncated list as a string representation
        return str(truncated) + ('...' if len(args_str) > limit else '')
    except Exception:
        return args_str


def extract_tool_response(message):
    """
    Extract and truncate the tool response from a log message.
    Args:
        message (str): The log message.
    Returns:
        str: Formatted tool response string, or a default message if not found.
    """
    # Search for the "Tool Message" section in the log message
    match = re.search(r"Name:\s*(\w+)\s*(.*)", message, re.DOTALL)
    if match:
        tool_name = match.group(1)
        response = match.group(2).strip()
        # Truncate the response if necessary
        truncated_response = truncate_tool_response(response)
        return f"Tool: {tool_name}, Response: {truncated_response}"
    return "No tool response found"


def truncate_tool_response(response_str, limit=100):
    """
    Truncate the tool response string to a specified character limit.
    Args:
        response_str (str): The response string.
        limit (int): Maximum number of characters to keep.
    Returns:
        str: Truncated response string.
    """
    # Truncate the response if it's too long
    if len(response_str) > limit:
        return response_str[:limit] + '...'
    return response_str
