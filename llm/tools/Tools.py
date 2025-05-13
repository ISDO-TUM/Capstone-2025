from langchain.agents import Tool
from paper_handling.paper_metadata_retriever import get_multiple_topic_works_titles
from paper_ranking.paper_ranker import select_relevant_titles

tools = [
    Tool(
        name="get_multiple_topic_works_titles",
        func=get_multiple_topic_works_titles,
        description=
        """Call this tool first to get a set of paper titles related to the user query, 
            add all the differnt user interests in the 'queries' input string array of this function
        """ 
        + get_multiple_topic_works_titles.__doc__
    ),
    Tool(
        name="select_relevant_titles",
        func= select_relevant_titles,
        description="Call this tool second to select the most relevant paper titles" + select_relevant_titles.__doc__
    )
]

def get_tools():
    return tools