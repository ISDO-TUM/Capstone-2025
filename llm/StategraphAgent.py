"""
Stategraph-based agent entrypoint for orchestrating multi-step academic paper search and filtering.

This module implements the main agent workflow for academic paper recommendation, including:
- Input handling and state initialization
- Out-of-scope query detection
- Query quality control (QC) and reformulation
- Multi-step reasoning and subquery expansion
- Paper ingestion and update for projects
- Vector similarity search and ranking
- Natural language filtering and top-10 selection
- Storing recommendations and summaries for projects
- Robust error handling and logging at each node

The agent is designed to be modular, extensible, and easy to debug or extend for new research flows.
"""

import logging
import json

# --- State schema ---
# The state is a dict with the following keys:
# - user_query: str
# - keywords: list[str] (optional)
# - reformulated_query: str (optional)
# - papers_raw: list[dict] (optional)
# - papers_filtered: list[dict] (optional)
# - final_output: dict (optional)

from llm.nodes.input import input_node  # noqa: E402  # isort:skip
from llm.nodes.out_of_scope_check import out_of_scope_check_node  # noqa: E402  # isort:skip
from llm.nodes.out_of_scope_handler import out_of_scope_handler_node  # noqa: E402  # isort:skip
from llm.nodes.quality_control import quality_control_node  # noqa: E402  # isort:skip
from llm.nodes.expand_subqueries import expand_subqueries_node  # noqa: E402  # isort:skip
from llm.nodes.get_best_papers import get_best_papers_node  # noqa: E402  # isort:skip
from llm.nodes.update_papers_by_project import update_papers_by_project_node  # noqa: E402  # isort:skip
from llm.nodes.filter_papers import filter_papers_node  # noqa: E402  # isort:skip
from llm.nodes.no_results_handler import no_results_handler_node  # noqa: E402  # isort:skip
from llm.nodes.store_papers_for_project import store_papers_for_project_node  # noqa: E402  # isort:skip

logger = logging.getLogger("StategraphAgent")
logger.setLevel(logging.INFO)


def trigger_stategraph_agent_show_thoughts(user_message: str):
    """
    Generator that yields each step of the Stategraph agent's thought process for frontend streaming.
    Args:
        user_message (str): The user's research query or message.
    Yields:
        dict: Thought and state at each step, including final output.
    """
    try:
        # Initialize state
        state = {"user_query": user_message}

        # Step 1: Input node
        yield {
            "thought": "Processing user input...",
            "is_final": False,
            "final_content": None,
        }
        state = input_node(state)

        # Step 2: Out-of-scope check
        yield {
            "thought": "Checking if query is within scope...",
            "is_final": False,
            "final_content": None,
        }
        state = out_of_scope_check_node(state)

        # Extract keywords from out_of_scope_result if available
        out_of_scope_result = state.get("out_of_scope_result")
        if out_of_scope_result:
            try:
                parsed = json.loads(out_of_scope_result)
                if parsed.get("status") == "valid" and "keywords" in parsed:
                    state["keywords"] = parsed["keywords"]
                    yield {
                        "thought": f"Extracted keywords: {state['keywords']}",
                        "is_final": False,
                        "final_content": None,
                    }
            except Exception as e:
                logger.error(f"Error parsing out_of_scope_result: {e}")

        # Step 3: Quality control
        yield {
            "thought": "Performing quality control and filter detection...",
            "is_final": False,
            "final_content": None,
        }
        state = quality_control_node(state)

        # Check if query is out of scope
        qc_decision = state.get("qc_decision", "accept")
        if qc_decision == "out_of_scope":
            yield {
                "thought": "Query determined to be out of scope. Generating explanation...",
                "is_final": False,
                "final_content": None,
            }
            state = out_of_scope_handler_node(state)

            # Return out-of-scope message
            out_of_scope_message = state.get("out_of_scope_message", {})
            yield {
                "thought": "Query rejected as out of scope. Please provide a new query.",
                "is_final": True,
                "final_content": json.dumps(
                    {
                        "type": "out_of_scope",
                        "message": out_of_scope_message,
                        "requires_user_input": True,
                    }
                ),
            }
            return

        # If split, expand subqueries
        if qc_decision == "split":
            yield {
                "thought": "Splitting query into subqueries...",
                "is_final": False,
                "final_content": None,
            }
            state = expand_subqueries_node(state)

        # Step 4: Update papers
        yield {
            "thought": "Updating paper database with latest research...",
            "is_final": False,
            "final_content": None,
        }
        state = update_papers_by_project_node(state)

        # Step 5: Get best papers
        yield {
            "thought": "Retrieving most relevant papers...",
            "is_final": False,
            "final_content": None,
        }
        state = get_best_papers_node(state)

        # Step 6: Filter papers
        yield {
            "thought": "Applying filters to refine results...",
            "is_final": False,
            "final_content": None,
        }
        state = filter_papers_node(state)

        # Check for no results
        papers_filtered = state.get("papers_filtered", [])
        if not papers_filtered:
            yield {
                "thought": "No papers found after filtering. Generating smart no-results explanation...",
                "is_final": False,
                "final_content": None,
            }
            state = no_results_handler_node(state)
            no_results_message = state.get("no_results_message", {})
            yield {
                "thought": "No papers found. Please try broadening your search or adjusting your filter.",
                "is_final": True,
                "final_content": json.dumps(
                    {
                        "type": "no_results",
                        "message": no_results_message,
                        "requires_user_input": True,
                    }
                ),
            }
            return

        # Final step: store papers for project
        yield {
            "thought": "Storing recommended papers for this project...",
            "is_final": False,
            "final_content": None,
        }
        state = store_papers_for_project_node(state)
        store_result = state.get("store_papers_result", "No result")
        yield {
            "thought": "Agent workflow complete.",
            "is_final": True,
            "final_content": json.dumps({"status": store_result}),
        }
    except Exception as e:
        logger.error(f"Error in Stategraph agent: {e}")
        yield {
            "thought": f"An error occurred: {str(e)}",
            "is_final": True,
            "final_content": None,
        }
