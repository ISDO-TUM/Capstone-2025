from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm_pydantic.state import AgentState
from llm_pydantic.tooling.tooling_mock import AgentDeps


@dataclass(slots=True)
class RetrievePapersNode(BaseNode[AgentState, AgentDeps]):
    """Pulls a lightweight candidate set using the mock toolbelt."""

    async def run(
        self, ctx: GraphRunContext[AgentState, AgentDeps]
    ) -> FilterPapersNode:
        count = 50 if ctx.state.has_filter_instructions else 10

        ctx.state.papers_raw = ctx.deps.tools.retrieve_papers(
            ctx.state.user_query, count
        )

        return FilterPapersNode()


from llm_pydantic.nodes.filter_papers_node import FilterPapersNode  # noqa: E402  # isort:skip
