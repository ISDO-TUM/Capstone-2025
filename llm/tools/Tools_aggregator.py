from llm.tools.paper_handling_tools import (
    update_papers,
    accept,
    retry_broaden,
    narrow_query,
    reformulate_query,
    detect_out_of_scope_query,
    filter_papers_by_nl_criteria
)
from paper_ranking.paper_ranker import get_best_papers
from llm.tools.paper_handling_tools import update_papers, accept, retry_broaden, reformulate_query, detect_out_of_scope_query
from llm.tools.paper_ranker import get_best_papers

tools = [
    update_papers,
    get_best_papers,
    accept,
    retry_broaden,
    narrow_query,
    reformulate_query,
    detect_out_of_scope_query,
    filter_papers_by_nl_criteria
]


def get_tools():
    return tools
