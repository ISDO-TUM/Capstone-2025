from pyalex import Works

def get_works(query, count=5):
    works = Works().search(query).filter(is_oa=True).sort(cited_by_count="desc")
    return [work for i, work in enumerate(works.get()) if i < count]

