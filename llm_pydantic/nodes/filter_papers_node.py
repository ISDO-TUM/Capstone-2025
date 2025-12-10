from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm_pydantic.state import AgentState
from llm_pydantic.tooling import AgentDeps


@dataclass(slots=True)
class FilterPapersNode(BaseNode[AgentState, AgentDeps]):
    """Apply natural language style filters to the candidates."""

    async def run(
        self, ctx: GraphRunContext[AgentState, AgentDeps]
    ) -> StorePapersNode | NoResultsNode:
        filtered, criteria = ctx.deps.tools.filter_papers(
            ctx.state.user_query,
            ctx.state.papers_raw,
            ctx.state.has_filter_instructions,
        )
        ctx.state.papers_filtered = filtered
        if not filtered:
            ctx.state.no_results_summary = criteria.get(
                "explanation", "Filters removed every candidate"
            )
            ctx.state.requires_user_input = True
            return NoResultsNode()
        return StorePapersNode()


from llm_pydantic.nodes.no_results_node import NoResultsNode  # noqa: E402  # isort:skip
from llm_pydantic.nodes.store_papers_node import StorePapersNode  # noqa: E402  # isort:skip
