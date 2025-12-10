from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm_pydantic.state import AgentState
from llm_pydantic.tooling import AgentDeps


@dataclass(slots=True)
class InputNode(BaseNode[AgentState, AgentDeps]):
    """Parse the raw query and collect lightweight metadata."""

    user_message: str

    async def run(self, ctx: GraphRunContext[AgentState, AgentDeps]) -> ScopeCheckNode:
        cleaned = self.user_message.strip()
        ctx.state.user_query = cleaned
        if "project id:" in cleaned.lower():
            query, _, project_id = cleaned.rpartition("project ID:")
            ctx.state.user_query = query.strip()
            ctx.state.project_id = project_id.strip()
        ctx.state.keywords = ctx.deps.tools.extract_keywords(ctx.state.user_query)
        return ScopeCheckNode()


# Imported late to avoid circular type checking issues with pydantic_graph.
from llm_pydantic.nodes.scope_node import ScopeCheckNode  # noqa: E402  # isort:skip
