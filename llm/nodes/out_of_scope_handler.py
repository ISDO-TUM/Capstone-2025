from __future__ import annotations

import logging
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, GraphRunContext

from llm.LLMDefinition import LLM
from llm.node_logger import NodeLogger
from llm.state import AgentOutput, AgentState

logger = logging.getLogger("out_of_scope_handler_node")
logger.setLevel(logging.INFO)

# --- Out-of-Scope Handler Node ---


node_logger = NodeLogger(
    "out_of_scope_handler",
    input_keys=["user_query", "qc_decision_reason"],
    output_keys=["out_of_scope_message", "requires_user_input", "error"],
)


@dataclass()
class OutOfScopeHandler(BaseNode[AgentState]):
    """
    Handle out-of-scope queries by providing explanation and requesting new input.
    Args:
        state (dict): The current agent state.
    Returns:
        dict: Updated state with out_of_scope_message and requires_user_input.
    """

    async def run(self, ctx: GraphRunContext[AgentState]) -> End[AgentOutput]:  # ty:ignore[invalid-method-override]
        state = ctx.state

        node_logger.log_begin(state.__dict__)

        user_query = state.user_query
        qc_decision_reason = (
            state.qc_decision_reason
            if state.qc_decision_reason
            else "The query was determined to be out of scope."
        )

        # Generate explanation for why the query was rejected
        explanation_prompt = f"""
        The user query "{user_query}" was determined to be out of scope for academic paper recommendations.

        Reason: {qc_decision_reason}

        Provide a helpful explanation to the user about why their query is out of scope and suggest how they could rephrase it to get relevant academic paper recommendations.

        Focus on:
        1. Why the current query doesn't work for academic paper search
        2. What types of queries work well (research topics, academic fields, specific technologies)
        3. Examples of better ways to phrase their request

        Keep the explanation friendly and constructive.
        """

        # Generate a short summary explanation
        short_explanation_prompt = f"""
        The user query "{user_query}" was determined to be out of scope for academic paper recommendations.
        Reason: {qc_decision_reason}

        In 1-2 short sentences, summarize for the user why their query is out of scope and what they should do instead. Be concise and direct (e.g., 'Your query is too general. Please specify a research topic or field.').
        """

        try:
            explanation_response = LLM.invoke(explanation_prompt)
            explanation = (
                explanation_response.content
                if hasattr(explanation_response, "content")
                else str(explanation_response)
            )

            short_explanation_response = LLM.invoke(short_explanation_prompt)
            short_explanation = (
                short_explanation_response.content
                if hasattr(short_explanation_response, "content")
                else str(short_explanation_response)
            )

            # Create the out-of-scope message
            out_of_scope_message = {
                "type": "out_of_scope",
                "original_query": user_query,
                "short_explanation": short_explanation,
                "explanation": explanation,
                "suggestion": "Please provide a new query focused on academic research topics, technologies, or fields of study.",
            }

            state.out_of_scope_message = out_of_scope_message
            state.requires_user_input = True

            logger.info(f"Out-of-scope query handled. Original query: '{user_query}'")

        except Exception as e:
            logger.error(f"Error in out_of_scope_handler_node: {e}")
            state.error = f"Error handling out-of-scope query: {e}"
            state.out_of_scope_message = {
                "type": "out_of_scope",
                "original_query": user_query,
                "short_explanation": "Your query is out of scope. Please specify a research topic or field.",
                "explanation": "The query was determined to be out of scope for academic paper recommendations. Please try a different query focused on research topics or academic fields.",
                "suggestion": "Please provide a new query focused on academic research topics, technologies, or fields of study.",
            }
            state.requires_user_input = True

        node_logger.log_end(state.__dict__)

        return End(AgentOutput("out of scope"))
