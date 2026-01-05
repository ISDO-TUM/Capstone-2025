from llm.nodes.node_logger import node_logger

# --- Node: Input Handler ---


@node_logger(
    "input_node", input_keys=["user_query"], output_keys=["user_query", "keywords"]
)
def input_node(state):
    """
    Initialize the state with the user query and extract project_id if present.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with user_query, keywords, and project_id.
    """
    # Initialize the state with the user query
    user_query = state["user_query"]
    # Extract project_id if appended to the user_query (e.g., '... project ID: <id>')
    project_id = None
    if "project ID:" in user_query:
        parts = user_query.rsplit("project ID:", 1)
        user_query = parts[0].strip()
        project_id = parts[1].strip()
    # If the query is a single word or phrase, use it as the initial keyword
    keywords = []
    if user_query and len(user_query.split()) == 1:
        keywords = [user_query]
    # Add project_id to state
    return {
        "user_query": user_query,
        "keywords": keywords,
        "reformulated_query": None,
        "papers_raw": [],
        "papers_filtered": [],
        "final_output": None,
        "project_id": project_id,
    }
