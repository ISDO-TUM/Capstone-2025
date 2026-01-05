import json
import logging

logger = logging.getLogger("expand_subqueries_node")
logger.setLevel(logging.INFO)


def expand_subqueries_node(state):
    """
    If the QC decision was 'split', extract subqueries and keywords from the multi_step_reasoning tool result.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with extracted subqueries.
    """
    qc_tool_result = state.get("qc_tool_result")
    subqueries = []
    if qc_tool_result:
        try:
            parsed = (
                json.loads(qc_tool_result)
                if isinstance(qc_tool_result, str)
                else qc_tool_result
            )
            if parsed.get("status") == "success" and "subqueries" in parsed:
                for sub in parsed["subqueries"]:
                    subqueries.append(
                        {
                            "description": sub.get("sub_description", ""),
                            "keywords": sub.get("keywords", []),
                        }
                    )
        except Exception as e:
            logger.error(f"Error parsing subqueries: {e}")
    state["subqueries"] = subqueries
    logger.info(f"Extracted {len(subqueries)} subqueries from split.")
    return state
