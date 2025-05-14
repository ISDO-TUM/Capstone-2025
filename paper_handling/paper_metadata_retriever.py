from pyalex import Works

def get_works(query, count=5):
    works = Works().search(query).filter(is_oa=True).sort(cited_by_count="desc")
    return [work for i, work in enumerate(works.get()) if i < count]

def get_multiple_topic_works(queries, count = 30):
    """
    query: expects an array of query strings
    """
    works = []
    for query in queries:
        works.append(get_works(query, count))
    return works

def get_works_titles(works):
    """
    works: array of Work objects. The Work objects correspond to a single topic
    """
    titles = []
    for work in works:
        titles.append(work['title'])
    return titles

def get_mulitple_topic_works_titles(works):
    """
    works: array of Work objects arrays, each Work sub array corresponds to a different topic
    """
    titles= []
    for topic_work in works:
        titles.extend(get_works_titles(topic_work))
    
    return titles

#works = get_multiple_topic_works(['generative AI', 'computer vision'])
#print(get_mulitple_topic_works_titles(works))


    

