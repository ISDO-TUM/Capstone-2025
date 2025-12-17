from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm_pydantic.state import AgentState
from llm_pydantic.tooling.tooling_mock import AgentDeps


@dataclass(slots=True)
class InputNode(BaseNode[AgentState, AgentDeps]):
    """Parse the raw query and collect lightweight metadata."""

    user_message: str

    async def run(self, ctx: GraphRunContext[AgentState, AgentDeps]) -> ScopeCheckNode:
        message = self.user_message.strip().lower()

        if "project id:" in message:
            before, _, after = message.partition(":")
            ctx.state.project_id = after.strip()
            ctx.state.user_query = before.replace("project id", "").strip()
        else:
            ctx.state.user_query = message

        ctx.state.keywords = ctx.deps.tools.extract_keywords(ctx.state.user_query)

        return ScopeCheckNode()


# Imported late to avoid circular type checking issues with pydantic_graph.
from llm_pydantic.nodes.scope_node import ScopeCheckNode  # noqa: E402  # isort:skip
