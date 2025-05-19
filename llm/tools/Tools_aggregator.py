from langchain.agents import Tool
from llm.tools.paper_handling_tools import get_paper_titles
from paper_ranking.paper_ranker import select_relevant_titles

tools = [
    get_paper_titles,
    select_relevant_titles
]

def get_tools():
    return tools