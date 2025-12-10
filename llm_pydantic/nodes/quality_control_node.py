from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm_pydantic.state import AgentState
from llm_pydantic.tooling import AgentDeps


@dataclass(slots=True)
class QualityControlNode(BaseNode[AgentState, AgentDeps]):
    """Leans on the mock toolbelt to sanity-check the query."""

    async def run(
        self, ctx: GraphRunContext[AgentState, AgentDeps]
    ) -> RetrievePapersNode | OutOfScopeNode:
        tools = ctx.deps.tools
        ctx.state.has_filter_instructions = tools.detect_filters(ctx.state.user_query)
        decision, reason = tools.qc_decision(ctx.state.user_query, ctx.state.keywords)
        ctx.state.qc_decision = decision
        ctx.state.qc_reason = reason
        if decision != "accept":
            ctx.state.out_of_scope_message = (
                "This prototype only proceeds when QC passes."
            )
            ctx.state.requires_user_input = True
            return OutOfScopeNode()
        return RetrievePapersNode()


from llm_pydantic.nodes.out_of_scope_node import OutOfScopeNode  # noqa: E402  # isort:skip
from llm_pydantic.nodes.retrieve_papers_node import RetrievePapersNode  # noqa: E402  # isort:skip
