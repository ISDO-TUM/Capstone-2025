from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, GraphRunContext

from llm_pydantic.state import AgentOutput, AgentState
from llm_pydantic.tooling import AgentDeps


@dataclass(slots=True)
class OutOfScopeNode(BaseNode[AgentState, AgentDeps, AgentOutput]):
    """Produce a friendly message when a query is rejected."""

    async def run(self, ctx: GraphRunContext[AgentState, AgentDeps]) -> End[AgentOutput]:
        payload = {
            "message": ctx.state.out_of_scope_message
            or "Please provide a research-focused question.",
            "reason": ctx.state.qc_reason,
            "requires_user_input": ctx.state.requires_user_input,
        }
        ctx.state.final_payload = payload
        return End(AgentOutput(status="out_of_scope", detail=payload))
