from pyalex import Works
from langchain_core.tools import tool

def get_works(query, count=5):
    """
    query: expects a string containing a query corresponding to a topic the paper API will get papers about
    count: the number of papers the paper API will get 
    """
    works = Works().search(query).filter(is_oa=True).sort(cited_by_count="desc")
    return [work for i, work in enumerate(works.get()) if i < count]

def get_multiple_topic_works(queries, count = 30):
    """
    query: expects an array of query strings. Each query is a topic the paper API will get papers about
    count: the number of papers the paper API will get for each topic
    """
    works = []
    for query in queries:
        works.append(get_works(query, count))
    return works

def get_works_titles(query, count=5):
    works = get_works(query, count)
    titles = []
    for work in works:
        titles.append(work['title'])
    return titles

@tool
def get_multiple_topic_works_titles(queries : list[str], count = 10) -> list[str]:
    """
    Gets a series of paper titles corresponding to a user's insterests. 

    Args:
        queries: must be a string array where each string corresponds to a topic of interest in form of one or a few keywords. Like: ['generative models', 'renewable energies', ...]
        count: int that corresponds to the number of paper titles returned per topic
    
    Return:
        The function returns a string array containing all the titles of all the found papers of all topics
    """
    print(f"Getting works with queries: {queries}")
    works = get_multiple_topic_works(queries, count)
    titles= []
    for topic_work in works:
        titles.extend(get_works_titles(topic_work))
    print(f"Found titles: {titles}")
    return titles

#works = get_multiple_topic_works(['generative AI', 'computer vision'])
#print(get_mulitple_topic_works_titles(works))


    

