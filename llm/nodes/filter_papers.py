from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm.node_logger import NodeLogger
from llm.state import AgentState
from llm.tools.Tools_aggregator import get_tools
from llm.tools.tooling_mock import AgentDeps

logger = logging.getLogger("filter_papers_node")
logger.setLevel(logging.INFO)


node_logger = NodeLogger(
    "filter_papers",
    input_keys=["user_query", "papers_raw", "has_filter_instructions"],
    output_keys=["papers_filtered", "applied_filter_criteria", "error"],
)


@dataclass()
class FilterPapers(BaseNode[AgentState, AgentDeps]):
    """
    Apply natural language filtering to the retrieved papers based on the user query.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with papers_filtered.
    """

    async def run(
        self, ctx: GraphRunContext[AgentState, AgentDeps]
    ) -> NoResultsHandler | StorePapersForProject:
        state = ctx.state

        node_logger.log_begin(state.__dict__)

        tools = get_tools()
        tool_map = {getattr(tool, "name", None): tool for tool in tools}
        filter_tool = tool_map.get("filter_papers_by_nl_criteria")
        papers_filtered = []

        try:
            user_query = state.user_query
            papers_raw = state.papers_raw
            has_filter_instructions = state.has_filter_instructions

            if not has_filter_instructions or not papers_raw:
                # No filtering needed or no papers to filter
                papers_filtered = papers_raw
                logger.info(
                    f"No filtering applied. Papers count: {len(papers_filtered)}"
                )
                state.applied_filter_criteria = {}
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
                            papers_filtered = filter_result_parsed.get(
                                "kept_papers", []
                            )
                            logger.info(
                                f"Applied filter. Kept {len(papers_filtered)} out of {len(papers_raw)} papers"
                            )
                            # Store the filter spec (filters) in the state for later use
                            state.applied_filter_criteria = filter_result_parsed.get(
                                "filters", {}
                            )
                        else:
                            logger.warning(
                                f"Filter failed: {filter_result_parsed.get('message', 'Unknown error')}"
                            )
                            papers_filtered = papers_raw
                            state.applied_filter_criteria = {}
                    except Exception as e:
                        logger.error(f"Error parsing filter result: {e}")
                        papers_filtered = papers_raw
                        state.applied_filter_criteria = {}
                else:
                    logger.warning("Filter tool not found")
                    papers_filtered = papers_raw
                    state.applied_filter_criteria = {}

            # Limit filtered papers to top 10 to maintain consistency with other recommendation flows
            original_count = len(papers_filtered)
            papers_filtered = papers_filtered[:10]
            state.papers_filtered = papers_filtered
            logger.info(
                f"Limited filtered papers from {original_count} to {len(papers_filtered)} (top 10)"
            )

        except Exception as e:
            state.error = f"Filter papers node error: {e}"
            state.papers_filtered = state.papers_raw
            state.applied_filter_criteria = {}

        node_logger.log_end(state.__dict__)

        # Check for no results
        papers_filtered = ctx.state.papers_filtered

        if not papers_filtered:
            return NoResultsHandler()
        else:
            return StorePapersForProject()


from llm.nodes.no_results_handler import NoResultsHandler  # noqa: E402 # isort:skip
from llm.nodes.store_papers_for_project import StorePapersForProject  # noqa: E402 # isort:skip
