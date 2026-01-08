from __future__ import annotations

import logging
from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm.node_logger import NodeLogger
from llm.state import AgentState
from llm.tools.Tools_aggregator import get_tools
from llm_pydantic.tooling.tooling_mock import AgentDeps

logger = logging.getLogger("get_best_papers_node")
logger.setLevel(logging.INFO)

# --- Get Best Papers Node ---


node_logger = NodeLogger(
    "get_best_papers",
    input_keys=["project_id", "has_filter_instructions"],
    output_keys=["papers_raw", "error"],
)


@dataclass()
class GetBestPapers(BaseNode[AgentState, AgentDeps]):
    """
    Retrieve the most relevant papers for a project based on filter instructions.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with papers_raw.
    """

    async def run(self, ctx: GraphRunContext[AgentState, AgentDeps]) -> FilterPapers:
        state = ctx.state

        node_logger.log_begin(state.__dict__)

        tools = get_tools()
        tool_map = {getattr(tool, "name", None): tool for tool in tools}
        get_best_papers_tool = tool_map.get("get_best_papers")
        papers_raw = []
        try:
            # Prefer keywords if available, else use user_query

            project_id = state.project_id

            # Determine retrieval count based on filter instructions
            has_filter_instructions = state.has_filter_instructions
            retrieval_count = (
                50 if has_filter_instructions else 10
            )  # More papers if filtering will be applied

            if get_best_papers_tool:
                # Use num_candidates parameter based on filter instructions
                papers_raw = get_best_papers_tool.invoke(
                    {"project_id": project_id, "num_candidates": retrieval_count}
                )

                logger.info(
                    f"Retrieved {len(papers_raw)} papers (filter instructions: {has_filter_instructions}, requested: {retrieval_count})"
                )

            state.papers_raw = papers_raw
        except Exception as e:
            state.error = f"Get best papers node error: {e}"

        node_logger.log_end(state.__dict__)

        return FilterPapers()


from llm.nodes.filter_papers import FilterPapers  # noqa: E402 # isort:skip
