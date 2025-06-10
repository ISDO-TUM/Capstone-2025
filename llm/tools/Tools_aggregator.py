from llm.tools.paper_handling_tools import get_paper_basic_data
from paper_ranking.paper_ranker import select_relevant_titles

tools = [
    get_paper_basic_data,
    select_relevant_titles
]


def get_tools():
    return tools
