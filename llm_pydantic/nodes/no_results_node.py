from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, GraphRunContext

from llm_pydantic.state import AgentOutput, AgentState
from llm_pydantic.tooling.tooling_mock import AgentDeps


@dataclass(slots=True)
class NoResultsNode(BaseNode[AgentState, AgentDeps, AgentOutput]):
    """Return a structured no-results payload."""

    async def run(
        self, ctx: GraphRunContext[AgentState, AgentDeps]
    ) -> End[AgentOutput]:
        reason = (
            getattr(ctx.state, "no_results_summary", None)
            or "No papers matched the query."
        )

        payload = {
            "type": "no_results",
            "reason": reason,
            "suggestion": "Try loosening the filters or changing the timeframe.",
        }

        ctx.state.final_payload = payload

        return End(AgentOutput(status="no_results", detail=payload))
