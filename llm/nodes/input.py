from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm.node_logger import NodeLogger
from llm.state import AgentState
from llm_pydantic.tooling.tooling_mock import AgentDeps

# --- Node: Input Handler ---


node_logger = NodeLogger(
    "input_node",
    input_keys=["user_query"],
    output_keys=["user_query", "keywords", "project_id"],
)


@dataclass()
class Input(BaseNode[AgentState, AgentDeps]):
    """
    Initialize the state with the user query and extract project_id if present.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with user_query, keywords, and project_id.
    """

    user_message: str

    async def run(self, ctx: GraphRunContext[AgentState, AgentDeps]) -> OutOfScopeCheck:
        state = ctx.state
        user_query = self.user_message

        node_logger.log_begin(state.__dict__)

        # Extract project_id if appended to the user_query (e.g., '... project ID: <id>')
        project_id = None
        if "project ID:" in user_query:
            parts = user_query.rsplit("project ID:", 1)
            user_query = parts[0].strip()
            project_id = parts[1].strip()
        # If the query is a single word or phrase, use it as the initial keyword
        keywords = []
        if user_query and len(user_query.split()) == 1:
            keywords = [user_query]
        # Add project_id to state

        state.user_query = user_query
        state.project_id = project_id
        state.keywords = keywords

        node_logger.log_end(state.__dict__)

        return OutOfScopeCheck()


from llm.nodes.out_of_scope_check import OutOfScopeCheck  # noqa: E402 # isort:skip
