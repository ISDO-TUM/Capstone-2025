from llm.tools.paper_handling_tools import update_papers
from paper_ranking.paper_ranker import get_best_papers
from Notification.PubSub import last_week_date, rank_and_filter_similar_papers, split_ranked_papers

tools = [
    update_papers,
    get_best_papers
]

pubsub_tools = [
    last_week_date,
    update_papers,
    get_best_papers,
    rank_and_filter_similar_papers,
    split_ranked_papers

]


def get_tools():
    return tools

def get_pub_sub_tools():
    return pubsub_tools