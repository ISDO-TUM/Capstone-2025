from llm.tools.paper_handling_tools import (
    update_papers,
    accept,
    retry_broaden,
    narrow_query,
    reformulate_query,
    detect_out_of_scope_query,
    multi_step_reasoning,
    filter_by_user_defined_metrics
)
from paper_ranking.paper_ranker import get_best_papers

tools = [
    update_papers,
    get_best_papers,
    accept,
    retry_broaden,
    narrow_query,
    reformulate_query,
    detect_out_of_scope_query,
    multi_step_reasoning,
    filter_by_user_defined_metrics
]


def get_tools():
    return tools
