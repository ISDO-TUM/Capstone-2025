from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm.node_logger import NodeLogger
from llm.state import AgentState
from llm.tools.paper_handling_tools import update_papers_for_project
from llm.tools.tooling_mock import AgentDeps

logger = logging.getLogger("update_papers_by_project_node")
logger.setLevel(logging.INFO)

# --- Update Papers by Project Node ---


node_logger = NodeLogger(
    "update_papers_by_project",
    input_keys=[
        "user_query",
        "qc_decision",
        "qc_tool_result",
        "project_id",
        "subqueries",
        "keywords",
    ],
    output_keys=["update_papers_by_project_result", "all_papers", "error"],
)


@dataclass()
class UpdatePapersByProject(BaseNode[AgentState, AgentDeps]):
    """
    Update the paper database for a specific project based on the user query and QC decision.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with update_papers_by_project_result.
    """

    async def run(self, ctx: GraphRunContext[AgentState, AgentDeps]) -> GetBestPapers:
        state = ctx.state

        node_logger.log_begin(state.__dict__)

        update_papers_by_project_result = None
        all_papers = []
        project_id = state.project_id
        try:
            # If subqueries exist, process each
            subqueries = state.subqueries or []
            if subqueries:
                update_results = []
                for sub in subqueries:
                    keywords = sub.get("keywords", [])
                    if project_id:
                        result = await update_papers_for_project(
                            queries=keywords, project_id=project_id
                        )
                        update_results.append(result)
                update_papers_by_project_result = update_results
            else:
                # Fallback: single query as before
                queries = []
                if state.qc_decision == "reformulate" and state.qc_tool_result:
                    try:
                        qc_result = json.loads(state.qc_tool_result)
                        if (
                            "result" in qc_result
                            and "refined_keywords" in qc_result["result"]
                        ):
                            queries = qc_result["result"]["refined_keywords"]
                        elif "reformulated_description" in qc_result:
                            queries = [qc_result["reformulated_description"]]
                    except Exception as e:
                        print(e)
                        queries = [state.user_query]
                elif state.qc_decision == "split" and state.qc_tool_result:
                    # Should not happen, handled above
                    queries = [state.user_query]
                else:
                    # Use keywords if available, otherwise fall back to user query
                    if state.keywords:
                        queries = state.keywords
                    else:
                        queries = [state.user_query]
                if project_id:
                    logger.info(
                        f"Calling update_papers_for_project with queries: {queries} and project_id: {project_id}"
                    )
                    update_papers_by_project_result = await update_papers_for_project(
                        queries=queries, project_id=project_id
                    )
                    logger.info(
                        f"update_papers_for_project result: {update_papers_by_project_result}"
                    )
            state.update_papers_by_project_result = update_papers_by_project_result
            state.all_papers = all_papers
        except Exception as e:
            state.error = f"Update papers by project node error: {e}"

        node_logger.log_end(state.__dict__)
        return GetBestPapers()


from llm.nodes.get_best_papers import GetBestPapers  # noqa: E402 # isort:skip
