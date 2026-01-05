from llm.nodes.node_logger import node_logger
from llm.tools.Tools_aggregator import get_tools

# --- Out-of-Scope Check Node ---


@node_logger(
    "out_of_scope_check", input_keys=["user_query"], output_keys=["out_of_scope_result"]
)
def out_of_scope_check_node(state):
    """
    Detect if the user query is out of scope for academic paper recommendations.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with out_of_scope_result.
    """
    # Get the detect_out_of_scope_query tool
    tools = get_tools()
    detect_out_of_scope_query = None
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "detect_out_of_scope_query":
            detect_out_of_scope_query = tool
            break
    if detect_out_of_scope_query is None:
        state["error"] = "detect_out_of_scope_query tool not found"
        return state

    # Call the tool
    result = detect_out_of_scope_query.invoke(
        {"query_description": state["user_query"]}
    )
    state["out_of_scope_result"] = result
    return state
