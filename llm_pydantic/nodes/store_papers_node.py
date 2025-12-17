from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, GraphRunContext

from llm_pydantic.state import AgentOutput, AgentState
from llm_pydantic.tooling.tooling_mock import AgentDeps


@dataclass(slots=True)
class StorePapersNode(BaseNode[AgentState, AgentDeps, AgentOutput]):
    """Persist (mock) recommendations and finish the run."""

    async def run(
        self, ctx: GraphRunContext[AgentState, AgentDeps]
    ) -> End[AgentOutput]:
        papers = ctx.state.papers_filtered or ctx.state.papers_raw
        result = ctx.deps.tools.store(ctx.state.project_id, papers)
        payload = {
            "type": "papers",
            "items": papers,
            "storage_result": result,
        }
        ctx.state.final_payload = payload
        return End(AgentOutput(status="success", detail=payload))
