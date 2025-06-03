from typing import Any

from paper_handling.paper_handler import fetch_works_multiple_queries


def get_paper_basic_data(queries: list[str]) -> list[dict[str, Any]]:
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
        A list of paper data (title, link) with corresponding to papers related to all the queries.
    """
    paper_metadata = fetch_works_multiple_queries(queries)
    paper_titles = [work["title"] for work in paper_metadata]
    paper_links = [_get_link(work) for work in paper_metadata]

    paper_basic_data = [{'title': title, 'link': link} for title, link in zip(paper_titles, paper_links)]
    return paper_basic_data


def _get_link(work):
    """
    This function takes a paper work object and returns its link
    Args:
        work: an open alex work object

    Returns: the link of the work either doi, oa_url, open alex url or None.

    """
    link = work.get('doi')
    if not link:
        link = work.get('open_access', {}).get('oa_url')
    if not link:
        link = work.get('landing_page_url')
    if not link:
        if work.get('id') and work.get('id').startswith('http'):
            link = work.get('id')
        else:
            link = "#"
    return link


def check_relevance_threshold(papers_with_relevance_scores: list[dict], threshold: float) -> bool:
    """
    Step 5: Checks if the similarity scores in the list of papers meet the specified threshold.
    Returns True if results are satisfactory, False otherwise.

    Args:
        papers_with_relevance_scores: A list of dictionaries where each dict represents a paper and includes a 'similarity_score' key.
        threshold: The minimum similarity score required for a paper to be considered relevant.

    Returns:
        True if all relevant papers meet the threshold (uses top 3 if available), otherwise False.
    """
    top_papers = papers_with_relevance_scores[:3] if len(papers_with_relevance_scores) > 3 else papers_with_relevance_scores
    return all(paper.get("similarity_score", 0.0) >= threshold for paper in top_papers)


def decide_next_action(papers_with_metadata: list[dict]) -> str:
    """
    Step 6: Agent logic to decide what to do next if results are not satisfactory.
    Returns one of: "retry_broaden", "reformulate_query", "lower_threshold", or "accept".
    """

    formatted_metadata = "\n\n".join(
        f"""Paper {i+1}:
            - Title: {paper.get("title", "N/A")}
            - Similarity Score: {paper.get("similarity_score", "N/A")}
            - Citation Count: {paper.get("cited_by_count", "N/A")}
            - FWCI: {paper.get("fwci", "N/A")}
            - Abstract: {paper.get("abstract", "N/A")}"""
        for i, paper in enumerate(papers_with_metadata)
    )

    prompt = f"""
    You are an intelligent research assistant responsible for evaluating a set of research papers returned from a query.

    For each paper, you have access to metadata such as:
    - similarity score (relevance to the original query),
    - citation count,
    - field-weighted citation impact (FWCI),
    - title,
    - abstract.

    Your goal is to assess whether the current set of results is satisfactory, or whether another action should be taken.

    Please choose **one** of the following actions based on the quality and relevance of the papers:
    - "accept": The papers are relevant and high-quality.
    - "retry_broaden": The papers are too narrow or too few, try a broader version of the current query.
    - "reformulate_query": The current query is off, and should be reformulated to better capture the user intent.
    - "lower_threshold": The threshold for similarity or quality might be too high, and lowering it could yield more useful results.

    You may consider papers satisfactory if:
    - Most have high similarity scores (e.g. > 0.7),
    - They include recent and well-cited research,
    - They align well with the query topic as indicated by abstract and title.

    Now decide based on the following paper metadata:

    {formatted_metadata}
    """

    # You would then feed `prompt` into your LLM to get the agent’s decision
    return prompt  # Replace this line with LLM completion call if integrating with an agent



def retry_with_modified_parameters(action: str, current_query: str, attempt: int) -> str:
    """
    Step 7: Based on the agent’s decision, generates the next query or parameters.
    References the output of `decide_next_action`.
    """

    if action == "accept":
        return current_query  # No change needed, accept the current query

    elif action == "retry_broaden":
        # Broaden the query by adding more general terms or synonyms
        broadened_query = f"{current_query} broadening search terms"
        return broadened_query

    elif action == "reformulate_query":
        # Reformulate the query to better capture user intent
        reformulated_query = f"Reformulated: {current_query} with better keywords"
        return reformulated_query

    elif action == "lower_threshold":
        # Lower the threshold for relevance scores
        new_threshold = 0.5  # Example of lowering the threshold
        return f"{current_query} with threshold {new_threshold}"

    else:
        raise ValueError(f"Unknown action: {action}")
    

def quality_control_loop(paper_candidates: list[dict], current_query: str, attempt: int = 0) -> list[dict]:
    """
    Wraps steps 5–7 together.
    - Calls `check_relevance_threshold`
    - If False, calls `decide_next_action`
    - Then `retry_with_modified_parameters` and loops if necessary
    """
