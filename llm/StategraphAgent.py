"""
Stategraph-based agent entrypoint for orchestrating multi-step academic paper search and filtering.
"""

import logging

# from langgraph.graph import StateGraph
# from langchain_core.messages import HumanMessage
# from llm.LLMDefinition import LLM
from llm.tools.Tools_aggregator import get_tools

# --- State schema ---
# The state is a dict with the following keys:
# - user_query: str
# - keywords: list[str] (optional)
# - reformulated_query: str (optional)
# - papers_raw: list[dict] (optional)
# - papers_filtered: list[dict] (optional)
# - final_output: dict (optional)

# --- Error handling and logging decorator ---


def node_logger(node_name, input_keys=None, output_keys=None):
    def decorator(func):
        def wrapper(state):
            logger = logging.getLogger("StategraphAgent")
            # Log input state
            if input_keys:
                logger.info(f"[{node_name}] Input: %s", {k: state.get(k) for k in input_keys})
            else:
                logger.info(f"[{node_name}] Input: %s", state)
            try:
                result = func(state)
                # Log output state
                if output_keys:
                    logger.info(f"[{node_name}] Output: %s", {k: result.get(k) for k in output_keys})
                else:
                    logger.info(f"[{node_name}] Output: %s", result)
                return result
            except Exception as e:
                logger.exception(f"[{node_name}] Exception occurred: %s", e)
                state["error"] = str(e)
                return state
        return wrapper
    return decorator

# --- Example usage on a node ---


@node_logger("input_node", input_keys=["user_query"], output_keys=["user_query", "keywords"])
def input_node(state):
    # Initialize the state with the user query
    return {
        "user_query": state["user_query"],
        "keywords": [],
        "reformulated_query": None,
        "papers_raw": [],
        "papers_filtered": [],
        "final_output": None
    }

# --- Out-of-Scope Check Node ---


@node_logger("out_of_scope_check", input_keys=["user_query"], output_keys=["out_of_scope_result"])
def out_of_scope_check_node(state):
    # Get the detect_out_of_scope_query tool
    tools = get_tools()
    detect_out_of_scope_query = None
    for tool in tools:
        if hasattr(tool, 'name') and tool.name == 'detect_out_of_scope_query':
            detect_out_of_scope_query = tool
            break
    if detect_out_of_scope_query is None:
        state["error"] = "detect_out_of_scope_query tool not found"
        return state

    # Call the tool
    result = detect_out_of_scope_query.invoke({"query_description": state["user_query"]})
    state["out_of_scope_result"] = result
    return state

# --- Quality Control Node (QC) ---


@node_logger("quality_control", input_keys=["user_query", "out_of_scope_result"], output_keys=["qc_decision", "qc_tool_result"])
def quality_control_node(state):
    import json
    tools = get_tools()
    # Map tool names to tool objects
    tool_map = {getattr(tool, 'name', None): tool for tool in tools}
    qc_decision = "accept"  # Default
    qc_tool_result = None
    try:
        result = state.get("out_of_scope_result")
        user_query = state.get("user_query", "")
        if result:
            parsed = json.loads(result)
            if parsed.get("status") == "out_of_scope":
                qc_decision = "out_of_scope"
                qc_tool_result = result
                state["qc_decision"] = qc_decision
                state["qc_tool_result"] = qc_tool_result
                return state
        # Simple heuristics for demo purposes
        if len(user_query.split()) < 5:
            # Too vague, reformulate
            qc_decision = "reformulate"
            tool = tool_map.get("reformulate_query")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query, "keywords": []})
        elif " and " in user_query or "," in user_query:
            # Multi-topic, split
            qc_decision = "split"
            tool = tool_map.get("multi_step_reasoning")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query})
        elif "specific" in user_query or "very narrow" in user_query:
            # Too narrow, broaden
            qc_decision = "broaden"
            tool = tool_map.get("retry_broaden")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query, "keywords": []})
        elif "too broad" in user_query or "many topics" in user_query:
            # Too broad, narrow
            qc_decision = "narrow"
            tool = tool_map.get("narrow_query")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query, "keywords": []})
        else:
            # Accept as is
            qc_decision = "accept"
            tool = tool_map.get("accept")
            if tool:
                qc_tool_result = tool.invoke({"confirmation": "yes"})
    except Exception as e:
        state["error"] = f"QC node error: {e}"
        qc_decision = "error"
    state["qc_decision"] = qc_decision
    state["qc_tool_result"] = qc_tool_result
    return state


def run_stategraph_agent(user_query: str):
    # This function will initialize the state, run the graph, and return the result
    # (To be implemented in the next steps)
    pass


if __name__ == "__main__":
    # Example usage (stepwise test)
    queries = [
        "I am looking for papers in the field of machine learning in healthcare published after 2018.",  # accept
        "Hello world",  # out_of_scope
        "AI",  # reformulate (too short)
        "AI and robotics, healthcare",  # split (multi-topic)
        "A very narrow and specific topic in quantum computing",  # broaden
        "This is too broad and covers many topics in science"  # narrow
    ]
    for user_query in queries:
        print(f"\n=== Testing query: '{user_query}' ===")
        # Step 1: Input node
        state = {"user_query": user_query}
        state = input_node(state)
        print("After input_node:", state)
        # Step 2: Out-of-scope check node
        state = out_of_scope_check_node(state)
        print("After out_of_scope_check_node:", state)
        # Step 3: Quality control node
        state = quality_control_node(state)
        print("After quality_control_node:", state)
