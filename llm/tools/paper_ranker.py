import json
import logging
from llm.Embeddings import embed_user_profile
from langchain_core.tools import tool
from chroma_db.chroma_vector_db import chroma_db
from database.papers_database_handler import get_papers_by_hash
from database.projects_database_handler import get_user_profile_embedding, add_user_profile_embedding, get_project_data

logger = logging.getLogger(__name__)


@tool
def get_best_papers(user_profile: str) -> list[dict]:
    """
    Tool Name: get_best_papers
    Returns a list of recommended papers based on the user profile.

    Args:
        user_profile (str): The user's input or research interests, or a project_id to use stored embedding.

    Returns:
        List[Dict]: A list of paper metadata dictionaries.
    """
    try:
        embedded_profile = get_user_profile_embedding(user_profile)

        if embedded_profile:
            logger.info(f"Using stored embedding for project {user_profile}")
        else:
            logger.info(f"No embedding found for project {user_profile}, creating one...")
            project_data = get_project_data(user_profile)
            description = project_data.get('description') if project_data else None

            if not description:
                logger.error(f"No project description found for project {user_profile}")
                return []

            embedded_profile = embed_user_profile(description)
            if not embedded_profile:
                logger.error(f"Failed to create embedding for project {user_profile}")
                return []

            add_user_profile_embedding(user_profile, embedded_profile)
            logger.info(f"Created and saved embedding for project {user_profile}")

    except Exception as e:
        logger.error(f"Error getting or creating user profile embedding for project {user_profile}: {e}")
        return []

    if not embedded_profile:
        logger.warning("Embedded profile is None, aborting process.")
        return []

    try:
        paper_hashes = chroma_db.perform_similarity_search(10, embedded_profile)

    except Exception as e:
        logger.error(f"Error performing similarity search: {e}")
        return []

    if not paper_hashes:
        logger.info("No similar papers found.")
        return []

    try:
        paper_metadata = get_papers_by_hash(paper_hashes)
        logger.info(f"Paper metadata: {paper_metadata}")
    except Exception as e:
        logger.error(f"Error linking hashes to metadata: {e}")
        return []

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
