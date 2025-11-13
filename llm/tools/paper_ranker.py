"""
This module implements tools for vector search and ranking of academic papers.

Responsibilities:
- Performing similarity search in ChromaDB using project/user profile embeddings
- Fetching and returning paper metadata in the correct similarity order
- Providing ranking and selection utilities for downstream recommendation flows

All ranking and retrieval tools are designed to be used by the Stategraph agent and other orchestration flows.
"""

import logging
from llm.Embeddings import embed_user_profile
from langchain_core.tools import tool
from chroma_db.chroma_vector_db import chroma_db
from database.papers_database_handler import get_papers_by_hash, get_all_papers
from database.projects_database_handler import (
    get_user_profile_embedding,
    add_user_profile_embedding,
    get_project_data,
)

logger = logging.getLogger(__name__)


@tool
def get_best_papers(project_id: str, num_candidates: int = 10) -> list[dict]:
    """
    Tool Name: get_best_papers
    Returns a list of recommended papers based on the project ID. If the agent want to apply filtering, the agent will increase the
    number of candidates to a higher number, e.g. 100 or 1000. To ensure that the agent can still return a reasonable number of papers, the default is set to 10.

    Args:
        project_id (str): The project ID to get papers for and to fetch the user profile embedding.
        num_candidates (int): The number of candidate papers to return (default 10).
    Returns:
        list[dict]: List of paper metadata dictionaries, ordered by similarity.
    Side effects:
        May create and store a new user profile embedding if not present.
    """
    try:
        embedded_profile = get_user_profile_embedding(project_id)

        if embedded_profile:
            logger.info(f"Using stored embedding for project {project_id}")
        else:
            logger.info(f"No embedding found for project {project_id}, creating one...")
            project_data = get_project_data(project_id)
            description = project_data.get("description") if project_data else None

            if not description:
                logger.error(f"No project description found for project {project_id}")
                return []

            embedded_profile = embed_user_profile(description)
            if not embedded_profile:
                logger.error(f"Failed to create embedding for project {project_id}")
                return []

            add_user_profile_embedding(project_id, embedded_profile)
            logger.info(f"Created and saved embedding for project {project_id}")

    except Exception as e:
        logger.error(
            f"Error getting or creating user profile embedding for project {project_id}: {e}"
        )
        return []

    if not embedded_profile:
        logger.warning("Embedded profile is None, aborting process.")
        return []

    try:
        if num_candidates != 10:
            logger.info(
                f"Agent requested {num_candidates} candidates, which is different than the default of 10. This will allow for more filtering."
            )

        paper_hashes = chroma_db.perform_similarity_search(
            num_candidates, embedded_profile
        )
        logger.info(
            f"Similarity search returned {len(paper_hashes) if paper_hashes else 0} hashes (requested: {num_candidates})"
        )

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
        logger.info(
            f"Number of papers found: {len(paper_metadata) if paper_metadata else 0}"
        )

        # Debug: Check if any of the hashes exist in the database
        if not paper_metadata and paper_hashes:
            all_papers = get_all_papers()
            all_hashes = [
                p.get("paper_hash") for p in all_papers if p.get("paper_hash")
            ]
            logger.info(f"Sample hashes in database: {all_hashes[:3]}")
            logger.info(
                f"Any matching hashes: {any(h in all_hashes for h in paper_hashes[:3])}"
            )

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
