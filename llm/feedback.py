from typing import List
import numpy as np


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


# if __name__ == "__main__":
#     user_vector = [0.1, 0.3, 0.5]
#     paper_vector = [0.4, 0.2, 0.6]
#
#     new_user_vector = update_user_vector(user_vector, paper_vector, rating=4)
#     print(new_user_vector)
