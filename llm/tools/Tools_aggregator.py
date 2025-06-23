from llm.tools.paper_handling_tools import (
    update_papers,
    accept,
    retry_broaden,
    narrow_query,
    reformulate_query,
    detect_out_of_scope_query
)
from paper_ranking.paper_ranker import get_best_papers

tools = [
    update_papers,
    get_best_papers,
    accept,
    retry_broaden,
    narrow_query,
    reformulate_query,
    detect_out_of_scope_query
]


def get_tools():
    return tools
