from llm.tools.paper_handling_tools import update_papers
from paper_ranking.paper_ranker import get_best_papers
from Notification.PubSub import last_week_date, rank_and_filter_similar_papers, split_ranked_papers
from Notification.SendMail import sendmail
from paper_handling.database_handler import get_papers_after_date
tools = [
    update_papers,
    get_best_papers
]

pubsub_tools = [
    last_week_date,
    update_papers,
    get_papers_after_date,
    get_best_papers,
    rank_and_filter_similar_papers,
    split_ranked_papers,
    sendmail

]


def get_tools():
    return tools

def get_pub_sub_tools():
    return pubsub_tools