import json
import logging

from llm.nodes.node_logger import node_logger
from llm.tools.Tools_aggregator import get_tools

logger = logging.getLogger("update_papers_by_project_node")
logger.setLevel(logging.INFO)

# --- Update Papers by Project Node ---


@node_logger(
    "update_papers_by_project",
    input_keys=["user_query", "qc_decision", "qc_tool_result", "project_id"],
    output_keys=["update_papers_by_project_result"],
)
def update_papers_by_project_node(state):
    """
    Update the paper database for a specific project based on the user query and QC decision.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with update_papers_by_project_result.
    """
    tools = get_tools()
    tool_map = {getattr(tool, "name", None): tool for tool in tools}
    update_papers_for_project_tool = tool_map.get("update_papers_for_project")
    logger.info(f"Available tool names: {list(tool_map.keys())}")
    logger.info(
        f"Looking for tool: update_papers_for_project, found: {update_papers_for_project_tool is not None}"
    )
    update_papers_by_project_result = None
    all_papers = []
    project_id = state.get("project_id")
    try:
        # If subqueries exist, process each
        subqueries = state.get("subqueries", [])
        if subqueries:
            update_results = []
            for sub in subqueries:
                keywords = sub.get("keywords", [])
                if update_papers_for_project_tool and project_id:
                    result = update_papers_for_project_tool.invoke(
                        {"queries": keywords, "project_id": project_id}
                    )
                    update_results.append(result)
            update_papers_by_project_result = update_results
        else:
            # Fallback: single query as before
            queries = []
            if state.get("qc_decision") == "reformulate" and state.get(
                "qc_tool_result"
            ):
                try:
                    qc_result = json.loads(state["qc_tool_result"])
                    if (
                        "result" in qc_result
                        and "refined_keywords" in qc_result["result"]
                    ):
                        queries = qc_result["result"]["refined_keywords"]
                    elif "reformulated_description" in qc_result:
                        queries = [qc_result["reformulated_description"]]
                except Exception:
                    queries = [state.get("user_query", "")]
            elif state.get("qc_decision") == "split" and state.get("qc_tool_result"):
                # Should not happen, handled above
                queries = [state.get("user_query", "")]
            else:
                # Use keywords if available, otherwise fall back to user query
                if state.get("keywords"):
                    queries = state["keywords"]
                else:
                    queries = [state.get("user_query", "")]
            if update_papers_for_project_tool and project_id:
                logger.info(
                    f"Calling update_papers_for_project with queries: {queries} and project_id: {project_id}"
                )
                update_papers_by_project_result = update_papers_for_project_tool.invoke(
                    {"queries": queries, "project_id": project_id}
                )
                logger.info(
                    f"update_papers_for_project result: {update_papers_by_project_result}"
                )
        state["update_papers_by_project_result"] = update_papers_by_project_result
        state["all_papers"] = all_papers
    except Exception as e:
        state["error"] = f"Update papers by project node error: {e}"
    return state
