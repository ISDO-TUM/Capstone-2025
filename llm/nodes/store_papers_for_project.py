from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, GraphRunContext

from llm.node_logger import NodeLogger
from llm.state import AgentOutput, AgentState
from llm.tools.paper_handling_tools import generate_relevance_summary
from llm.tools.Tools_aggregator import get_tools

node_logger = NodeLogger(
    "store_papers_for_project",
    input_keys=["project_id", "papers_filtered", "papers_raw", "user_query"],
    output_keys=["store_papers_for_project_result"],
)


@dataclass()
class StorePapersForProject(BaseNode[AgentState]):
    """
    Store the recommended papers for a project in the database.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with store_papers_for_project_result.
    """

    async def run(self, ctx: GraphRunContext[AgentState]) -> End[AgentOutput | None]:  # ty:ignore[invalid-method-override]
        state = ctx.state

        node_logger.log_begin(state.__dict__)

        tools = get_tools()
        tool_map = {getattr(tool, "name", None): tool for tool in tools}
        store_papers_for_project_tool = tool_map.get("store_papers_for_project")
        # Use filtered papers if available, else raw
        project_id = state.project_id
        papers = state.papers_filtered or state.papers_raw or []
        user_query = state.user_query
        # Prepare papers for storage: must include paper_hash and agent_summary
        papers_to_store = []
        for paper in papers:
            paper_hash = paper.get("hash") or paper.get("paper_hash")
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            # Use the tool version (invoke as a tool)
            try:
                summary = generate_relevance_summary.invoke(
                    {"user_query": user_query, "title": title, "abstract": abstract}
                )
            except Exception:
                summary = f"Relevant to project query: {user_query}"
            if paper_hash:
                papers_to_store.append({"paper_hash": paper_hash, "summary": summary})
        result = None
        if store_papers_for_project_tool and project_id and papers_to_store:
            result = store_papers_for_project_tool.invoke(
                {"project_id": project_id, "papers": papers_to_store}
            )
        else:
            result = "No papers to store or missing project_id."
        state.store_papers_for_project_result = result

        node_logger.log_end(state.__dict__)

        return End(AgentOutput(status="finished"))
