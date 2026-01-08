from __future__ import annotations

import json
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, GraphRunContext

from llm.LLMDefinition import LLM
from llm.node_logger import NodeLogger
from llm.state import AgentOutput, AgentState
from llm.tools.Tools_aggregator import get_tools

# --- Smart No-Results Handler Node ---


node_logger = NodeLogger(
    "no_results_handler",
    input_keys=[
        "user_query",
        "papers_raw",
        "papers_filtered",
        "applied_filter_criteria",
    ],
    output_keys=["no_results_message"],
)


@dataclass()
class NoResultsHandler(BaseNode[AgentState]):
    """
    If no papers are found after filtering, generate a smart explanation using the LLM.
    Finds the closest value for each filterable metric (year, citations, impact factor, etc.) using the find_closest_paper_metrics tool.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with no_results_message.
    """

    async def run(self, ctx: GraphRunContext[AgentState]) -> End[AgentOutput]:  # ty:ignore[invalid-method-override]
        state = ctx.state

        node_logger.log_begin(state.__dict__)

        user_query = state.user_query
        papers_raw = state.papers_raw
        # papers_filtered is used implicitly - we know it's empty when this node is called
        filter_criteria_json = state.applied_filter_criteria

        # Use the tool to get closest values and directions
        tools = get_tools()
        tool_map = {getattr(tool, "name", None): tool for tool in tools}
        closest_tool = tool_map.get("find_closest_paper_metrics")
        closest_values = {}
        if closest_tool:
            try:
                closest_result = closest_tool.invoke(
                    {"papers": papers_raw, "filter_spec": filter_criteria_json}
                )
                closest_values = json.loads(closest_result)
            except Exception:
                closest_values = {}

        # Compose a prompt for the LLM
        smart_explanation_prompt = f"""
        The user searched for academic papers with the following query:
        "{user_query}"
        After applying all filters, no papers were found.
        The filter criteria were: {json.dumps(filter_criteria_json)}
        The detailed analysis of available values: {json.dumps(closest_values)}

        IMPORTANT: Use the EXACT values provided above in your explanation. Do not make up generic values.

        Please explain to the user in a friendly, concise way:
        1. That no papers matched their combined filters (this is not an error)
        2. For each filter individually:
        - State the best available value for that metric
        - Whether any papers would match that filter alone
        - If papers would match individually, mention this as a potential adjustment
        3. Suggest specific adjustments based on the actual values:
        - If individual filters would work, suggest trying them separately
        - If values are close to thresholds, suggest lowering them slightly
        - If best available values are much better than thresholds, highlight this

        Be specific and use the actual numbers from the analysis data.
        """
        try:
            llm_response = LLM.invoke(smart_explanation_prompt)
            explanation = (
                llm_response.content
                if hasattr(llm_response, "content")
                else str(llm_response)
            )
            state.no_results_message = {
                "type": "no_results",
                "explanation": explanation,
                "closest_values": closest_values,
                "filter_criteria": filter_criteria_json,
            }
        except Exception:
            state.no_results_message = {
                "type": "no_results",
                "explanation": "No papers matched your filter. Please try broadening your search.",
                "closest_values": closest_values,
                "filter_criteria": filter_criteria_json,
            }

        node_logger.log_end(state.__dict__)

        return End(AgentOutput(status="no_results_handled"))
