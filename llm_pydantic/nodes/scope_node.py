from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm_pydantic.state import AgentState
from llm_pydantic.tooling.tooling_mock import AgentDeps


@dataclass(slots=True)
class ScopeCheckNode(BaseNode[AgentState, AgentDeps]):
    """Gate-keep obvious out-of-scope user queries."""

    async def run(
        self, ctx: GraphRunContext[AgentState, AgentDeps]
    ) -> QualityControlNode | OutOfScopeNode:
        is_out = ctx.deps.tools.detect_out_of_scope(ctx.state.user_query)

        if is_out:
            ctx.state.qc_decision = "out_of_scope"
            ctx.state.qc_reason = "Query contains topics outside academic search"
            ctx.state.out_of_scope_message = "We only handle academic paper discovery."
            ctx.state.requires_user_input = True
            return OutOfScopeNode()

        return QualityControlNode()


from llm_pydantic.nodes.out_of_scope_node import OutOfScopeNode  # noqa: E402  # isort:skip
from llm_pydantic.nodes.quality_control_node import QualityControlNode  # noqa: E402  # isort:skip
