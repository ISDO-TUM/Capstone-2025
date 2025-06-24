from llm.tools.paper_handling_tools import accept, retry_broaden, reformulate_query, \
    detect_out_of_scope_query, update_papers_for_project, store_papers_for_project
from llm.tools.paper_ranker import get_best_papers

tools = [
    update_papers_for_project,
    get_best_papers,
    accept,
    retry_broaden,
    reformulate_query,
    detect_out_of_scope_query,
    store_papers_for_project,
]


def get_tools():
    return tools
