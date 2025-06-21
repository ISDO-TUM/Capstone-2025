from typing import List

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

    # Define how strongly the feedback should influence the update
    weight = (rating - 3) * 0.05  # from -0.1 (bad) to +0.1 (excellent)

    # Apply weighted update
    updated_vector = [
        u + weight * p
        for u, p in zip(user_vector, paper_vector)
    ]

    return updated_vector


if __name__ == "__main__":
    user_vector = [0.1, 0.3, 0.5]
    paper_vector = [0.4, 0.2, 0.6]

    new_user_vector = update_user_vector(user_vector, paper_vector, rating=4)
    print(new_user_vector)