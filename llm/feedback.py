from typing import List
import numpy as np
import logging
from database.projects_database_handler import get_user_profile_embedding, add_user_profile_embedding
from chroma_db.chroma_vector_db import chroma_db

logger = logging.getLogger(__name__)


def update_user_vector(user_vector: List[float], paper_vector: List[float], rating: int) -> List[float]:
    """
    Modify the user embedding vector based on feedback from rating a paper.

    Args:
        user_vector (List[float]): The user's current embedding.
        paper_vector (List[float]): The paper's embedding.
        rating (int): Feedback rating from 1 (bad) to 5 (excellent).

    Returns:
        List[float]: Updated user embedding vector.
    """

    # Compute weight: positive for good ratings, negative for bad ratings
    weight = (rating - 3) * 0.05

    # Convert to numpy for vectorized operations
    user_vec_np = np.array(user_vector)
    paper_vec_np = np.array(paper_vector)

    # Apply weighted update
    updated_vec_np = user_vec_np + weight * paper_vec_np

    # Normalize the updated vector to keep it on the unit sphere
    norm = np.linalg.norm(updated_vec_np)
    if norm > 0:
        updated_vec_np = updated_vec_np / norm

    return updated_vec_np.tolist()


def update_user_profile_embedding_from_rating(project_id: str, paper_hash: str, rating: int) -> bool:
    """
    Update the user profile embedding based on a paper rating.

    Args:
        project_id (str): The project ID
        paper_hash (str): The paper hash
        rating (int): The rating (1-5)

    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        # Get current user profile embedding
        current_embedding = get_user_profile_embedding(project_id)
        if current_embedding is None:
            logger.warning(f"No user profile embedding found for project {project_id}, skipping update")
            return False

        # Get paper embedding directly from ChromaDB
        paper_embedding = chroma_db.get_embedding_by_hash(paper_hash)
        if paper_embedding is None:
            logger.warning(f"No embedding found in ChromaDB for paper hash {paper_hash}, skipping update")
            return False

        # Update user profile embedding based on rating
        updated_embedding = update_user_vector(current_embedding, paper_embedding, rating)

        # Save updated embedding to database
        add_user_profile_embedding(project_id, updated_embedding)

        logger.info(f"Updated user profile embedding for project {project_id} based on rating {rating}")
        return True

    except Exception as e:
        logger.error(f"Failed to update user profile embedding for project {project_id}: {e}")
        return False


# if __name__ == "__main__":
#     user_vector = [0.1, 0.3, 0.5]
#     paper_vector = [0.4, 0.2, 0.6]
#
#     new_user_vector = update_user_vector(user_vector, paper_vector, rating=4)
#     print(new_user_vector)
