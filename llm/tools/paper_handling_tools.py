from paper_handling.paper_handler import fetch_works_multiple_queries

def get_paper_titles(queries: list[str]) -> list[str]:
    """
    This function takes a list of queries and returns a list of paper titles.
    Args:
        queries: A list of queries in form of string keywords corresponding to the user's interests.
        each query corresponds to a different interest field. Like: ['generative models', 'renewable energies', ...]
    Example input:
    {
      "queries": ["agriculture in Costa Rica", "Use of pesticides in central America", ...],
    }
    Returns:
        A list of paper titles with corresponding to papers related to all the queries.
    """
    paper_metadata = fetch_works_multiple_queries(queries)
    print(len(paper_metadata))
    paper_titles = [work["title"] for work in paper_metadata]
    return paper_titles



