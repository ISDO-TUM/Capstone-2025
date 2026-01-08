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

from __future__ import annotations

import asyncio
import json
import logging

from pydantic_graph import Graph

from llm.nodes.expand_subqueries import ExpandSubqueries
from llm.nodes.filter_papers import FilterPapers
from llm.nodes.get_best_papers import GetBestPapers
from llm.nodes.input import Input
from llm.nodes.no_results_handler import NoResultsHandler
from llm.nodes.out_of_scope_check import OutOfScopeCheck
from llm.nodes.out_of_scope_handler import OutOfScopeHandler
from llm.nodes.quality_control import QualityControl
from llm.nodes.store_papers_for_project import StorePapersForProject
from llm.nodes.update_papers_by_project import UpdatePapersByProject
from llm.state import AgentOutput, AgentState

logger = logging.getLogger("StategraphAgent")
logger.setLevel(logging.WARNING)


def build_agent_graph() -> Graph[AgentState, AgentOutput]:
    """Create the reusable graph instance for callers/tests."""

    return Graph(
        nodes=(
            ExpandSubqueries,
            FilterPapers,
            GetBestPapers,
            Input,
            NoResultsHandler,
            OutOfScopeCheck,
            OutOfScopeHandler,
            QualityControl,
            StorePapersForProject,
            UpdatePapersByProject,
        ),
        state_type=AgentState,
    )


async def run_agent(
    user_message: str,
    *,
    state: AgentState | None = None,
) -> AgentOutput:
    """Helper that runs the graph for a single query."""

    graph = build_agent_graph()
    run_state = state or AgentState()
    result = await graph.run(
        Input(user_message=user_message),
        state=run_state,
    )
    return result.output


def run_agent_sync(
    user_message: str,
    *,
    state: AgentState | None = None,
) -> AgentOutput:
    """Synchronous convenience wrapper for quick experiments."""

    return asyncio.run(run_agent(user_message, state=state))


async def trigger_stategraph_agent_show_thoughts_async(user_message: str):
    """
    Async generator that yields each step of the Pydantic agent's thought process for frontend streaming.

    Args:
        user_message (str): The user's research query or message.

    Yields:
        dict: Thought and state at each step, including final output.
    """
    try:
        # Initialize state and dependencies
        state = AgentState()
        graph = build_agent_graph()

        # Map node class names to user-friendly descriptions
        node_descriptions = {
            "Input": "Processing user input...",
            "OutOfScopeCheck": "Checking if query is within scope...",
            "QualityControl": "Performing quality control and filter detection...",
            "OutOfScopeHandler": "Query determined to be out of scope. Generating explanation...",
            "ExpandSubqueries": "Splitting query into subqueries...",
            "UpdatePapersByProject": "Updating paper database with latest research...",
            "GetBestPapers": "Retrieving most relevant papers...",
            "FilterPapers": "Applying filters to refine results...",
            "NoResultsHandler": "No papers found after filtering. Generating smart no-results explanation...",
            "StorePapersForProject": "Storing recommended papers for this project...",
        }

        # Run the graph with streaming events using iter context manager
        async with graph.iter(
            Input(user_message=user_message),
            state=state,
        ) as graph_run:
            previous_node_name = None
            async for node in graph_run:
                # Each event is a node instance (BaseNode or End)
                node_name = node.__class__.__name__

                # Check for special conditions based on state
                if previous_node_name == "OutOfScopeCheck" and state.keywords:
                    yield {
                        "thought": f"Extracted keywords: {state.keywords}",
                        "is_final": False,
                        "final_content": None,
                    }

                # Get description or use node name
                thought = node_descriptions.get(node_name, f"Running {node_name}...")

                previous_node_name = node_name

                if node_name != "End":
                    yield {
                        "thought": thought,
                        "is_final": False,
                        "final_content": None,
                    }

        # Check final state for special cases
        if state.qc_decision == "out_of_scope":
            yield {
                "thought": "Query rejected as out of scope. Please provide a new query.",
                "is_final": True,
                "final_content": json.dumps(
                    {
                        "type": "out_of_scope",
                        "message": state.out_of_scope_message or {},
                        "requires_user_input": True,
                    }
                ),
            }
            return

        if not state.papers_filtered:
            yield {
                "thought": "No papers found. Please try broadening your search or adjusting your filter.",
                "is_final": True,
                "final_content": json.dumps(
                    {
                        "type": "no_results",
                        "message": state.no_results_message or {},
                        "requires_user_input": True,
                    }
                ),
            }
            return

        # Success case
        yield {
            "thought": "Agent workflow complete.",
            "is_final": True,
            "final_content": json.dumps(
                {"status": str(state.store_papers_for_project_result or "No result")}
            ),
        }

    except Exception as e:
        logger.error(f"Error in Pydantic Stategraph agent: {e}")
        yield {
            "thought": f"An error occurred: {str(e)}",
            "is_final": True,
            "final_content": None,
        }


def trigger_stategraph_agent_show_thoughts(user_message: str):
    """
    Synchronous generator wrapper for trigger_stategraph_agent_show_thoughts_async.

    Args:
        user_message (str): The user's research query or message.

    Yields:
        dict: Thought and state at each step, including final output.
    """
    # Create a new event loop for this generator
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Get the async generator
        async_gen = trigger_stategraph_agent_show_thoughts_async(user_message)

        # Manually iterate through the async generator
        while True:
            try:
                # Get the next item from the async generator
                result = loop.run_until_complete(async_gen.__anext__())
                yield result
            except StopAsyncIteration:
                break
    finally:
        loop.close()
