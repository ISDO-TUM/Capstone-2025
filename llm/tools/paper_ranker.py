"""
This module implements tools for vector search and ranking of academic papers.

Responsibilities:
- Performing similarity search in ChromaDB using project/user profile embeddings
- Fetching and returning paper metadata in the correct similarity order
- Providing ranking and selection utilities for downstream recommendation flows

All ranking and retrieval tools are designed to be used by the Stategraph agent and other orchestration flows.
"""

import logging
from typing import List

from pydantic import BaseModel

from llm.LLMDefinition import TextAgent
from llm.Embeddings import embed_user_profile
from chroma_db.chroma_vector_db import chroma_db
from database.papers_database_handler import get_papers_by_hash
from database.projects_database_handler import (
    get_user_profile_embedding,
    add_user_profile_embedding,
    get_project_data,
    get_project_owner_id,
)

logger = logging.getLogger(__name__)


class GetBestPapersInput(BaseModel):
    project_id: str
    num_candidates: int = 10


class PaperMetadata(BaseModel):
    paper_hash: str
    title: str
    abstract: str
    authors: List[str] = []
    publication_date: str = ""
    landing_page_url: str = ""


class GetBestPapersOutput(BaseModel):
    papers: List[PaperMetadata]


@TextAgent.tool_plain
def get_best_papers(project_id: str, num_candidates: int = 10) -> GetBestPapersOutput:
    """
    Tool Name: get_best_papers
    Returns a list of recommended papers based on the project ID. If the agent wants to apply filtering,
    the agent can increase the number of candidates (e.g., 100 or 1000). Default is 10.
    """
    owner_id = get_project_owner_id(project_id)
    if not owner_id:
        logger.error(f"Unable to determine owner for project {project_id}")
        return GetBestPapersOutput(papers=[])

    try:
        embedded_profile = get_user_profile_embedding(owner_id, project_id)

        if embedded_profile:
            logger.info(f"Using stored embedding for project {project_id}")
        else:
            logger.info(f"No embedding found for project {project_id}, creating one...")
            project_data = get_project_data(owner_id, project_id)
            description = project_data.get("description") if project_data else None

            if not description:
                logger.error(f"No project description found for project {project_id}")
                return GetBestPapersOutput(papers=[])

            embedded_profile = embed_user_profile(description)
            if not embedded_profile:
                logger.error(f"Failed to create embedding for project {project_id}")
                return GetBestPapersOutput(papers=[])

            add_user_profile_embedding(owner_id, project_id, embedded_profile)
            logger.info(f"Created and saved embedding for project {project_id}")

    except Exception as e:
        logger.error(
            f"Error getting or creating user profile embedding for project {project_id}: {e}"
        )
        return GetBestPapersOutput(papers=[])

    if not embedded_profile:
        logger.warning("Embedded profile is None, aborting process.")
        return GetBestPapersOutput(papers=[])

    try:
        if num_candidates != 10:
            logger.info(
                f"Agent requested {num_candidates} candidates, which is different from the default of 10."
            )

        paper_hashes = chroma_db.perform_similarity_search(
            num_candidates, embedded_profile
        )
        logger.info(
            f"Similarity search returned {len(paper_hashes) if paper_hashes else 0} hashes (requested: {num_candidates})"
        )

    except Exception as e:
        logger.error(f"Error performing similarity search: {e}")
        return GetBestPapersOutput(papers=[])

    if not paper_hashes:
        logger.info("No similar papers found.")
        return GetBestPapersOutput(papers=[])

    try:
        # Debug: Check what hashes we're looking for
        logger.info(f"Looking for hashes: {paper_hashes[:3]}...")  # Show first 3

        paper_metadata_list = get_papers_by_hash(paper_hashes)
        logger.info(
            f"Number of papers found: {len(paper_metadata_list) if paper_metadata_list else 0}"
        )

    except Exception as e:
        logger.error(f"Error linking hashes to metadata: {e}")
        return GetBestPapersOutput(papers=[])

    # Transform raw dicts into Pydantic models
    papers = []
    for paper in paper_metadata_list or []:
        try:
            papers.append(PaperMetadata(**paper))
        except Exception as e:
            logger.warning(f"Skipping paper due to invalid format: {e}")

    return GetBestPapersOutput(papers=papers)
