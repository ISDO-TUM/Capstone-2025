import json
import logging

from llm.nodes.node_logger import node_logger
from llm.tools.Tools_aggregator import get_tools

logger = logging.getLogger("filter_papers_node")
logger.setLevel(logging.INFO)


# --- Filter Papers Node ---
@node_logger(
    "filter_papers",
    input_keys=["user_query", "papers_raw", "has_filter_instructions"],
    output_keys=["papers_filtered"],
)
def filter_papers_node(state):
    """
    Apply natural language filtering to the retrieved papers based on the user query.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with papers_filtered.
    """
    tools = get_tools()
    tool_map = {getattr(tool, "name", None): tool for tool in tools}
    filter_tool = tool_map.get("filter_papers_by_nl_criteria")
    papers_filtered = []

    try:
        user_query = state.get("user_query", "")
        papers_raw = state.get("papers_raw", [])
        has_filter_instructions = state.get("has_filter_instructions", False)

        if not has_filter_instructions or not papers_raw:
            # No filtering needed or no papers to filter
            papers_filtered = papers_raw
            logger.info(f"No filtering applied. Papers count: {len(papers_filtered)}")
            state["applied_filter_criteria"] = {}
        else:
            # Use the filter_papers_by_nl_criteria tool to get both filtered papers and the filter spec
            filter_extraction_nl = user_query
            if filter_tool:
                filter_result = filter_tool.invoke(
                    {"papers": papers_raw, "criteria_nl": filter_extraction_nl}
                )
                try:
                    filter_result_parsed = json.loads(filter_result)
                    if filter_result_parsed.get("status") == "success":
                        papers_filtered = filter_result_parsed.get("kept_papers", [])
                        logger.info(
                            f"Applied filter. Kept {len(papers_filtered)} out of {len(papers_raw)} papers"
                        )
                        # Store the filter spec (filters) in the state for later use
                        state["applied_filter_criteria"] = filter_result_parsed.get(
                            "filters", {}
                        )
                    else:
                        logger.warning(
                            f"Filter failed: {filter_result_parsed.get('message', 'Unknown error')}"
                        )
                        papers_filtered = papers_raw
                        state["applied_filter_criteria"] = {}
                except Exception as e:
                    logger.error(f"Error parsing filter result: {e}")
                    papers_filtered = papers_raw
                    state["applied_filter_criteria"] = {}
            else:
                logger.warning("Filter tool not found")
                papers_filtered = papers_raw
                state["applied_filter_criteria"] = {}

        # Limit filtered papers to top 10 to maintain consistency with other recommendation flows
        original_count = len(papers_filtered)
        papers_filtered = papers_filtered[:10]
        state["papers_filtered"] = papers_filtered
        logger.info(
            f"Limited filtered papers from {original_count} to {len(papers_filtered)} (top 10)"
        )

    except Exception as e:
        state["error"] = f"Filter papers node error: {e}"
        state["papers_filtered"] = state.get("papers_raw", [])
        state["applied_filter_criteria"] = {}

    return state
