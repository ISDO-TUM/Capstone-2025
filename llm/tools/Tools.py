from langchain.agents import Tool
from paper_handling.paper_metadata_retriever import get_multiple_topic_works_titles
from paper_ranking.paper_ranker import select_relevant_titles

tools = [
    get_multiple_topic_works_titles,
    select_relevant_titles
]

def get_tools():
    return tools