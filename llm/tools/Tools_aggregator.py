
from llm.tools.paper_handling_tools import (
    update_papers_for_project,
    accept,
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
    accept,
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
    return tools
