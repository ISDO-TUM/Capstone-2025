from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm.node_logger import NodeLogger
from llm.state import AgentState
from llm.tools.Tools_aggregator import get_tools
from llm_pydantic.tooling.tooling_mock import AgentDeps

logger = logging.getLogger("OutOfScopeCheck")
logger.setLevel(logging.WARNING)

# --- Out-of-Scope Check Node ---


node_logger = NodeLogger(
    "out_of_scope_check",
    input_keys=["user_query"],
    output_keys=["out_of_scope_result", "error"],
)


@dataclass()
class OutOfScopeCheck(BaseNode[AgentState, AgentDeps]):
    """
    Detect if the user query is out of scope for academic paper recommendations.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with out_of_scope_result.
    """

    async def run(self, ctx: GraphRunContext[AgentState, AgentDeps]) -> QualityControl:
        state = ctx.state

        node_logger.log_begin(state.__dict__)
        # Get the detect_out_of_scope_query tool
        tools = get_tools()
        detect_out_of_scope_query = None
        for tool in tools:
            if hasattr(tool, "name") and tool.name == "detect_out_of_scope_query":
                detect_out_of_scope_query = tool
                break
        if detect_out_of_scope_query is None:
            state.error = "detect_out_of_scope_query tool not found"
            return state

        # Call the tool
        result = detect_out_of_scope_query.invoke(
            {"query_description": state.user_query}
        )
        state.out_of_scope_result = result

        node_logger.log_end(state.__dict__)

        # Extract keywords from out_of_scope_result if available
        if state.out_of_scope_result:
            try:
                parsed = json.loads(state.out_of_scope_result)
                if parsed.get("status") == "valid" and "keywords" in parsed:
                    ctx.state.keywords = parsed["keywords"]
            except Exception as e:
                logger.error(f"Error parsing out_of_scope_result: {e}")

        return QualityControl()


from llm.nodes.quality_control import QualityControl  # noqa: E402 # isort:skip
