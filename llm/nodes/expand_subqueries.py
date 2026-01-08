from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm.node_logger import NodeLogger
from llm.state import AgentState
from llm_pydantic.tooling.tooling_mock import AgentDeps

logger = logging.getLogger("expand_subqueries_node")
logger.setLevel(logging.INFO)


node_logger = NodeLogger(
    "expand_subqueries",
    input_keys=["qc_tool_result"],
    output_keys=["subqueries"],
)


@dataclass()
class ExpandSubqueries(BaseNode[AgentState, AgentDeps]):
    """
    If the QC decision was 'split', extract subqueries and keywords from the multi_step_reasoning tool result.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with extracted subqueries.
    """

    async def run(
        self, ctx: GraphRunContext[AgentState, AgentDeps]
    ) -> UpdatePapersByProject:
        state = ctx.state
        node_logger.log_begin(state.__dict__)

        qc_tool_result = state.qc_tool_result
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
        state.subqueries = subqueries
        logger.info(f"Extracted {len(subqueries)} subqueries from split.")

        node_logger.log_end(state.__dict__)

        return UpdatePapersByProject()


from llm.nodes.update_papers_by_project import UpdatePapersByProject  # noqa: E402
