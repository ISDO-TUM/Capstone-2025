import logging

# --- Error handling and logging decorator ---

logger = logging.getLogger("node_logger")
logger.setLevel(logging.INFO)


def node_logger(node_name, input_keys=None, output_keys=None):
    """
    Decorator for logging input and output of stategraph agent nodes.
    Args:
        node_name (str): Name of the node for logging.
        input_keys (list, optional): Keys to log from the input state.
        output_keys (list, optional): Keys to log from the output state.
    Returns:
        function: Wrapped function with logging and error handling.
    """

    def decorator(func):
        def wrapper(state):
            logger = logging.getLogger("StategraphAgent")
            # Log input state
            if input_keys:
                logger.info(
                    f"[{node_name}] Input: %s", {k: state.get(k) for k in input_keys}
                )
            else:
                logger.info(f"[{node_name}] Input: %s", state)
            try:
                result = func(state)
                # Log output state
                if output_keys:
                    logger.info(
                        f"[{node_name}] Output: %s",
                        {k: result.get(k) for k in output_keys},
                    )
                else:
                    logger.info(f"[{node_name}] Output: %s", result)
                return result
            except Exception as e:
                logger.exception(f"[{node_name}] Exception occurred: %s", e)
                state["error"] = str(e)
                return state

        return wrapper

    return decorator
