from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext

from llm.LLMDefinition import LLM
from llm.node_logger import NodeLogger
from llm.state import AgentState
from llm.tools.paper_handling_tools import (
    multi_step_reasoning,
    narrow_query,
    reformulate_query,
    retry_broaden,
)
from llm.tools.tooling_mock import AgentDeps
from custom_logging import agent_logger
from custom_logging.utils import calculate_openai_cost

logger = logging.getLogger("quality_control_node")
logger.setLevel(logging.INFO)

# --- Quality Control Node (QC) ---


node_logger = NodeLogger(
    "quality_control",
    input_keys=["user_query", "out_of_scope_result", "keywords"],
    output_keys=[
        "qc_decision",
        "qc_tool_result",
        "keywords",
        "has_filter_instructions",
        "error",
    ],
)


@dataclass()
class QualityControl(BaseNode[AgentState, AgentDeps]):
    """
    Perform quality control and filter detection on the user query.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with QC decision, tool result, keywords, and filter instructions flag.
    """

    async def run(
        self, ctx: GraphRunContext[AgentState, AgentDeps]
    ) -> OutOfScopeHandler | ExpandSubqueries | UpdatePapersByProject:
        state = ctx.state

        node_logger.log_begin(state.__dict__)

        qc_decision = "accept"  # Default
        qc_tool_result = None
        try:
            result = state.out_of_scope_result
            user_query = state.user_query
            keywords = state.keywords

            # Extract keywords from out_of_scope_result if available
            if result:
                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, dict):
                        if parsed.get("status") == "out_of_scope":
                            qc_decision = "out_of_scope"
                            qc_tool_result = result
                            state.qc_decision = qc_decision
                            state.qc_tool_result = qc_tool_result
                            # Don't return here - let the LLM QC decision process continue
                        elif parsed.get("status") == "valid" and "keywords" in parsed:
                            keywords = parsed["keywords"]
                            state.keywords = keywords
                except Exception as e:
                    logger.error(f"Error parsing out_of_scope_result: {e}")

            # Update keywords in state
            state.keywords = keywords

            # Use LLM to intelligently detect filter instructions
            filter_detection_prompt = f"""
            You are an academic research assistant. Analyze the user query to determine if it contains filter instructions.

            Filter instructions include:
            - Date/time constraints: "after 2020", "before 2018", "published since 2022", "between 2019-2023"
            - Citation constraints: "highly cited", "more than 50 citations", "well-cited papers"
            - Author constraints: "by author X", "from researcher Y", "authored by"
            - Journal/conference constraints: "published in Nature", "from conference X", "in journal Y"
            - Impact constraints: "high impact", "top journals", "prestigious venues"
            - Similarity constraints: "highly relevant", "closely related", "similar to"
            - Specific metrics: "fwci > 5", "citation percentile > 90", "impact factor > 10"

            User query: "{user_query}"

            Respond with ONLY a JSON object:
            {{
            "has_filter_instructions": true/false,
            "reason": "brief explanation of why"
            }}
            """

            try:
                filter_response = await LLM(filter_detection_prompt)
                filter_response = LLM.invoke(filter_detection_prompt)
                metadata = {
                    "filter_detection_prompt": filter_detection_prompt,
                    # "filter_model_name": filter_response.response_metadata[
                    #     "model_name"
                    # ],
                    # "filter_input_tokens": filter_response.usage_metadata[
                    #     "input_tokens"
                    # ],
                    # "filter_output_tokens": filter_response.usage_metadata[
                    #     "output_tokens"
                    # ],
                    # "filter_total_tokens": filter_response.usage_metadata[
                    #     "total_tokens"
                    # ],
                    # "filter_total_cost_in_usd": calculate_openai_cost(
                    #     filter_response.usage_metadata["input_tokens"],
                    #     filter_response.usage_metadata["output_tokens"],
                    # ),
                }
                agent_logger.add_metadata(metadata=metadata)
                filter_response_content = (
                    filter_response.content
                    if hasattr(filter_response, "content")
                    else str(filter_response)
                )
                filter_result = (
                    json.loads(filter_response_content)
                    if isinstance(filter_response_content, str)
                    else filter_response_content
                )

                # Handle potential list response
                if isinstance(filter_result, list) and len(filter_result) > 0:
                    filter_result = filter_result[0]

                has_filter_instructions = False
                reason = "No reason provided"
                if isinstance(filter_result, dict):
                    has_filter_instructions = filter_result.get(
                        "has_filter_instructions", False
                    )
                    reason = filter_result.get("reason", "No reason provided")

                state.has_filter_instructions = has_filter_instructions
                agent_logger.add_metadata(
                    {
                        "filter_detection_result": has_filter_instructions,
                        "filter_detection_reason": reason,
                    }
                )
                logger.info(f"Filter detection: {has_filter_instructions} - {reason}")

            except Exception as e:
                logger.error(f"Error in filter detection: {e}")
                state.has_filter_instructions = False

            # LLM-driven QC decision
            qc_prompt = f"""
            You are an academic research assistant. Given the following user query and keywords, decide which action to take:
            - If the query is valid and specific, respond with 'accept'.
            - If the query is vague, respond with 'reformulate'.
            - If the query is too broad, respond with 'narrow'.
            - If the query is too narrow, respond with 'broaden'.
            - If the query contains multiple topics, respond with 'split'.
            - If the query is not a valid research topic, respond with 'out_of_scope'.

            User query: "{user_query}"
            Keywords: {keywords}

            Respond with a JSON object:
            {{
            "qc_decision": "accept" | "reformulate" | "broaden" | "narrow" | "split" | "out_of_scope",
            "reason": "..."
            }}
            """
            qc_response = await LLM(qc_prompt)
            metadata = {
                "qc_prompt": qc_prompt,
                # "qc_model_name": qc_response.response_metadata["model_name"],
                # "qc_input_tokens": qc_response.usage_metadata["input_tokens"],
                # "qc_output_tokens": qc_response.usage_metadata["output_tokens"],
                # "qc_total_tokens": qc_response.usage_metadata["total_tokens"],
                # "qc_total_cost_in_usd": calculate_openai_cost(
                #     qc_response.usage_metadata["input_tokens"],
                #     qc_response.usage_metadata["output_tokens"],
                # ),
            }
            agent_logger.add_metadata(metadata=metadata)
            qc_response_content = (
                qc_response.content
                if hasattr(qc_response, "content")
                else str(qc_response)
            )
            qc_result = (
                json.loads(qc_response_content)
                if isinstance(qc_response_content, str)
                else qc_response_content
            )
            # If qc_result is a list, use the first element if possible
            if isinstance(qc_result, list) and len(qc_result) > 0:
                qc_result = qc_result[0]
            if not isinstance(qc_result, dict):
                qc_result = {}
            qc_decision = qc_result.get("qc_decision", "accept")
            state.qc_decision = qc_decision
            state.qc_decision_reason = qc_result.get("reason", "")
            # Call the appropriate tool if needed
            if qc_decision == "reformulate":
                qc_tool_result = await reformulate_query(
                    query_description=user_query, keywords=keywords
                )
                try:
                    tool_result = (
                        json.loads(qc_tool_result)
                        if isinstance(qc_tool_result, str)
                        else qc_tool_result
                    )
                    if (
                        "result" in tool_result
                        and "refined_keywords" in tool_result["result"]
                    ):
                        state.keywords = tool_result["result"]["refined_keywords"]
                except Exception as e:
                    logger.error(f"Error in reformulate_query: {e}")
            elif qc_decision == "split":
                qc_tool_result = await multi_step_reasoning(
                    query_description=user_query
                )
            elif qc_decision == "broaden":
                qc_tool_result = await retry_broaden(
                    query_description=user_query, keywords=keywords
                )
                try:
                    tool_result = (
                        json.loads(qc_tool_result)
                        if isinstance(qc_tool_result, str)
                        else qc_tool_result
                    )
                    if "broadened_keywords" in tool_result:
                        state.keywords = tool_result["broadened_keywords"]
                except Exception as e:
                    logger.error(f"Error in retry_broaden: {e}")
            elif qc_decision == "narrow":
                qc_tool_result = await narrow_query(
                    query_description=user_query, keywords=keywords
                )
                try:
                    tool_result = (
                        json.loads(qc_tool_result)
                        if isinstance(qc_tool_result, str)
                        else qc_tool_result
                    )
                    if "narrowed_keywords" in tool_result:
                        state.keywords = tool_result["narrowed_keywords"]
                except Exception as e:
                    logger.error(f"Error in narrow_query: {e}")
            state.qc_tool_result = qc_tool_result
        except Exception as e:
            state.error = f"QC node error: {e}"
            qc_decision = "error"

        node_logger.log_end(state.__dict__)

        # Check if query is out of scope
        if state.qc_decision == "out_of_scope":
            return OutOfScopeHandler()

        # If split, expand subqueries
        if state.qc_decision == "split":
            return ExpandSubqueries()

        return UpdatePapersByProject()


from llm.nodes.out_of_scope_handler import OutOfScopeHandler  # noqa: E402 # isort:skip
from llm.nodes.expand_subqueries import ExpandSubqueries  # noqa: E402 # isort:skip
from llm.nodes.update_papers_by_project import UpdatePapersByProject  # noqa: E402 # isort:skip
