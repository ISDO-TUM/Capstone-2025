"""
Tool aggregator for the Capstone project LLM agent.

Responsibilities:
- Imports and registers all available tools for the agent
- Provides a single list of tools for agent orchestration and tool selection
- Used by both the StategraphAgent and legacy agent flows
"""

from llm.tools.paper_handling_tools import (
    update_papers_for_project,
    retry_broaden,
    narrow_query,
    reformulate_query,
    detect_out_of_scope_query,
    filter_papers_by_nl_criteria,
    store_papers_for_project,
    replace_low_rated_paper,
    find_closest_paper_metrics,
    multi_step_reasoning,
)
from llm.tools.paper_ranker import get_best_papers

tools = [
    update_papers_for_project,
    get_best_papers,
    retry_broaden,
    narrow_query,
    reformulate_query,
    store_papers_for_project,
    detect_out_of_scope_query,
    filter_papers_by_nl_criteria,
    replace_low_rated_paper,
    find_closest_paper_metrics,
    multi_step_reasoning,
]


def get_tools():
    """
    Return the list of all registered tools for the agent.
    Returns:
        list: List of tool objects.
    """
    return tools
