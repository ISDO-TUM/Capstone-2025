"""
Stategraph-based agent entrypoint for orchestrating multi-step academic paper search and filtering.
"""

import logging
import json

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

logger = logging.getLogger("StategraphAgent")
logger.setLevel(logging.INFO)


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

# --- Node: Input Handler ---


@node_logger("input_node", input_keys=["user_query"], output_keys=["user_query", "keywords"])
def input_node(state):
    # Initialize the state with the user query
    user_query = state["user_query"]
    # If the query is a single word or phrase, use it as the initial keyword
    keywords = []
    if user_query and len(user_query.split()) == 1:
        keywords = [user_query]
    return {
        "user_query": user_query,
        "keywords": keywords,
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


@node_logger("quality_control", input_keys=["user_query", "out_of_scope_result", "keywords"], output_keys=["qc_decision", "qc_tool_result", "keywords"])
def quality_control_node(state):
    from llm.LLMDefinition import LLM
    tools = get_tools()
    tool_map = {getattr(tool, 'name', None): tool for tool in tools}
    qc_decision = "accept"  # Default
    qc_tool_result = None
    try:
        result = state.get("out_of_scope_result")
        user_query = state.get("user_query", "")
        keywords = state.get("keywords", [])
        if result:
            parsed = json.loads(result)
            if isinstance(parsed, dict) and parsed.get("status") == "out_of_scope":
                qc_decision = "out_of_scope"
                qc_tool_result = result
                state["qc_decision"] = qc_decision
                state["qc_tool_result"] = qc_tool_result
                return state
        # LLM-driven QC decision
        qc_prompt = f"""
You are an academic research assistant. Given the following user query and keywords, decide which action to take:
- If the query is valid and specific, respond with 'accept'.
- If the query is vague, respond with 'reformulate'.
- If the query is too broad, respond with 'narrow'.
- If the query is too narrow, respond with 'broaden'.
- If the query contains multiple topics, respond with 'split'.
- If the query is not a valid research topic, respond with 'out_of_scope'.

User query: "{user_query}"
Keywords: {keywords}

Respond with a JSON object:
{{
  "qc_decision": "accept" | "reformulate" | "broaden" | "narrow" | "split" | "out_of_scope",
  "reason": "..."
}}
"""
        qc_response = LLM.invoke(qc_prompt)
        qc_result = json.loads(qc_response.content) if isinstance(qc_response.content, str) else qc_response.content
        # If qc_result is a list, use the first element if possible
        if isinstance(qc_result, list) and len(qc_result) > 0:
            qc_result = qc_result[0]
        if not isinstance(qc_result, dict):
            qc_result = {}
        qc_decision = qc_result.get("qc_decision", "accept")
        state["qc_decision"] = qc_decision
        state["qc_decision_reason"] = qc_result.get("reason", "")
        # Call the appropriate tool if needed
        if qc_decision == "reformulate":
            tool = tool_map.get("reformulate_query")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query, "keywords": keywords})
                try:
                    tool_result = json.loads(qc_tool_result) if isinstance(qc_tool_result, str) else qc_tool_result
                    if "result" in tool_result and "refined_keywords" in tool_result["result"]:
                        state["keywords"] = tool_result["result"]["refined_keywords"]
                except Exception as e:
                    logger.error(f"Error in ...: {e}")
        elif qc_decision == "split":
            tool = tool_map.get("multi_step_reasoning")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query})
        elif qc_decision == "broaden":
            tool = tool_map.get("retry_broaden")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query, "keywords": keywords})
                try:
                    tool_result = json.loads(qc_tool_result) if isinstance(qc_tool_result, str) else qc_tool_result
                    if "broadened_keywords" in tool_result:
                        state["keywords"] = tool_result["broadened_keywords"]
                except Exception as e:
                    logger.error(f"Error in ...: {e}")
        elif qc_decision == "narrow":
            tool = tool_map.get("narrow_query")
            if tool:
                qc_tool_result = tool.invoke({"query_description": user_query, "keywords": keywords})
                try:
                    tool_result = json.loads(qc_tool_result) if isinstance(qc_tool_result, str) else qc_tool_result
                    if "narrowed_keywords" in tool_result:
                        state["keywords"] = tool_result["narrowed_keywords"]
                except Exception as e:
                    logger.error(f"Error in ...: {e}")
        elif qc_decision == "accept":
            tool = tool_map.get("accept")
            if tool:
                qc_tool_result = tool.invoke({"confirmation": "yes"})
        state["qc_tool_result"] = qc_tool_result
    except Exception as e:
        state["error"] = f"QC node error: {e}"
        qc_decision = "error"
    return state

# --- Update Papers Node ---


@node_logger("update_papers", input_keys=["user_query", "qc_decision", "qc_tool_result"], output_keys=["update_papers_result"])
def update_papers_node(state):
    tools = get_tools()
    tool_map = {getattr(tool, 'name', None): tool for tool in tools}
    update_papers_tool = tool_map.get("update_papers")
    update_papers_result = None
    try:
        # Use reformulated query or user_query as input
        queries = []
        if state.get("qc_decision") == "reformulate" and state.get("qc_tool_result"):
            try:
                qc_result = json.loads(state["qc_tool_result"])
                if "result" in qc_result and "refined_keywords" in qc_result["result"]:
                    queries = qc_result["result"]["refined_keywords"]
                elif "reformulated_description" in qc_result:
                    queries = [qc_result["reformulated_description"]]
            except Exception:
                queries = [state.get("user_query", "")]
        elif state.get("qc_decision") == "split" and state.get("qc_tool_result"):
            try:
                qc_result = json.loads(state["qc_tool_result"])
                if "subqueries" in qc_result:
                    queries = [subq["sub_description"] for subq in qc_result["subqueries"]]
            except Exception:
                queries = [state.get("user_query", "")]
        else:
            queries = [state.get("user_query", "")]
        if update_papers_tool:
            update_papers_result = update_papers_tool.invoke({"queries": queries})
        state["update_papers_result"] = update_papers_result
    except Exception as e:
        state["error"] = f"Update papers node error: {e}"
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
        "Biology",  # reformulate (too short/vague)
        "Deep learning for genomics and climate change adaptation",  # split (multi-topic)
        "Quantum entanglement in nitrogen-vacancy centers at 4K in diamond nanostructures",  # broaden (very narrow)
        "Recent advances in science and technology"  # narrow (too broad)
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
        out_of_scope_result = state.get("out_of_scope_result")
        if out_of_scope_result:
            try:
                parsed = json.loads(out_of_scope_result)
                if parsed.get("status") == "valid" and "keywords" in parsed:
                    state["keywords"] = parsed["keywords"]
            except Exception as e:
                # Optionally log or handle parsing errors
                logger.error(f"Error in ...: {e}")
                pass
        print("After out_of_scope_check_node:", state)
        # Step 3: Quality control node
        state = quality_control_node(state)
        print("After quality_control_node:", state)
        # Step 4: Update papers node
        state = update_papers_node(state)
        print("After update_papers_node:", state)
