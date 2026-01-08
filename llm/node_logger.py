import json
import logging

# --- Error handling and logging decorator ---

logger = logging.getLogger("node_logger")
logger.setLevel(logging.INFO)


def _truncate_value(value, limit=20):
    try:
        serialized = json.dumps(value, default=str)
    except TypeError:
        serialized = str(value)
    return serialized[:limit] + ("..." if len(serialized) > limit else "")


def _truncate_payload(payload, limit=20):
    """Trim each value in payload to the limit for clearer logs."""
    if isinstance(payload, dict):
        return {k: _truncate_value(v, limit) for k, v in payload.items()}
    if isinstance(payload, list):
        return [_truncate_value(v, limit) for v in payload]
    return _truncate_value(payload, limit)


class NodeLogger:
    """Logger class for tracking node execution with configurable parameters."""

    def __init__(self, node_name, input_keys=None, output_keys=None, truncate_limit=20):
        """
        Initialize the NodeLogger.

        Args:
            node_name: Name of the node being logged
            input_keys: List of keys to extract from state for input logging
            output_keys: List of keys to extract from state for output logging
            truncate_limit: Maximum length for logged values
        """
        self.node_name = node_name
        self.input_keys = input_keys
        self.output_keys = output_keys
        self.truncate_limit = truncate_limit

    def log_begin(self, state) -> None:
        """Log the beginning of node execution."""
        input_payload = (
            {k: state.get(k) for k in self.input_keys} if self.input_keys else state
        )
        truncated_input = _truncate_payload(input_payload, self.truncate_limit)
        print(
            f"[{self.node_name}] Input: {json.dumps(truncated_input, default=str)}"
            if isinstance(truncated_input, (dict, list))
            else f"[{self.node_name}] Input: {truncated_input}"
        )

    def log_end(self, state) -> None:
        """Log the end of node execution."""
        output_payload = (
            {k: state.get(k) for k in self.output_keys} if self.output_keys else state
        )
        truncated_output = _truncate_payload(output_payload, self.truncate_limit)
        print(
            f"[{self.node_name}] Output: {json.dumps(truncated_output, default=str)}"
            if isinstance(truncated_output, (dict, list))
            else f"[{self.node_name}] Output: {truncated_output}"
        )
