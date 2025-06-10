from llm.tools.paper_handling_tools import update_papers
from llm.tools.paper_ranker import get_best_papers

tools = [
    update_papers,
    get_best_papers
]


def get_tools():
    return tools
