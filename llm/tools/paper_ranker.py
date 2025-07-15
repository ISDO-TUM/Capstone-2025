import json
import logging
from llm.Embeddings import embed_user_profile
from langchain_core.tools import tool
from chroma_db.chroma_vector_db import chroma_db
from database.papers_database_handler import get_papers_by_hash, get_all_papers

logger = logging.getLogger(__name__)


@tool
def get_best_papers(user_profile: str, num_candidates: int = 10) -> list[dict]:
    """
    Tool Name: get_best_papers
    Returns a list of recommended papers based on the user profile. If the agent want to apply filtering, the agent will increase the
    number of candidates to a higher number, e.g. 100 or 1000. To ensure that the agent can still return a reasonable number of papers, the default is set to 10.

    Args:
        user_profile (str): The user's input or research interests.
        num_candidates (int): The number of candidate papers to return. Default is 10.

    Returns:
        List[Dict]: A list of paper metadata dictionaries.
    """
    try:
        embedded_profile = embed_user_profile(user_profile)
    except Exception as e:
        logger.error(f"User profile could not be embedded: {e}")
        return []

    if embedded_profile is None:
        logger.warning("Embedded profile is None, aborting process.")
        return []

    try:
        if num_candidates != 10:
            logger.info(f"Agent requested {num_candidates} candidates, which is different than the default of 10. This will allow for more filtering.")

        paper_hashes = chroma_db.perform_similarity_search(num_candidates, embedded_profile)
        logger.info(
            f"Similarity search returned {len(paper_hashes) if paper_hashes else 0} hashes (requested: {num_candidates})")

    except Exception as e:
        logger.error(f"Error performing similarity search: {e}")
        return []

    if not paper_hashes:
        logger.info("No similar papers found.")
        return []

    try:
        # Debug: Check what hashes we're looking for
        logger.info(f"Looking for hashes: {paper_hashes[:3]}...")  # Show first 3

        paper_metadata = get_papers_by_hash(paper_hashes)
        logger.info(f"Paper metadata: {paper_metadata}")
        logger.info(f"Number of papers found: {len(paper_metadata) if paper_metadata else 0}")

        # Debug: Check if any of the hashes exist in the database
        if not paper_metadata and paper_hashes:
            all_papers = get_all_papers()
            all_hashes = [p.get('paper_hash') for p in all_papers if p.get('paper_hash')]
            logger.info(f"Sample hashes in database: {all_hashes[:3]}")
            logger.info(f"Any matching hashes: {any(h in all_hashes for h in paper_hashes[:3])}")

    except Exception as e:
        logger.error(f"Error linking hashes to metadata: {e}")
        return []

    # Debug: Check if there are any papers in the database
    try:
        all_papers = get_all_papers()
        logger.info(f"Total papers in database: {len(all_papers)}")
        if all_papers:
            logger.info(f"Sample paper hash: {all_papers[0].get('paper_hash', 'N/A')}")
    except Exception as e:
        logger.error(f"Error checking database state: {e}")

    return paper_metadata if paper_metadata else []

# DEPRECATED


@tool
def select_relevant_titles(input: str) -> str:
    """
    Input str should be a JSON string with:
      - 'papers': a list of paper titles and links dict
      - 'query': the user query or research interest

    Example:
    {
      "papers": [
        {
            "title":"Deep Learning in Medicine",
            "link": "example link"
        },
        {
            "title" : "Climate Change Models",
            "link": "example link"
        },
        {
            "title": "Transformer Architectures",
            "link": "example link"
        }],
      "query": "machine learning for healthcare"
    }

    Returns a comma-separated string of titles and links most relevant to the query.
    """

    try:
        data = json.loads(input)
        papers = data.get("papers", [])
        query = data.get("query", "")

        if not papers or not query:
            return "Missing 'papers' or 'query' in input."

        return f"Filter these papers: {papers} based on this query: '{query}', select the 5-10 most relevant ones"

    except Exception as e:
        return f"Error parsing input: {e}"
