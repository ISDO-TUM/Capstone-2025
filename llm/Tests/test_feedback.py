import numpy as np
from llm.Embeddings import embed_papers
from llm.feedback import update_user_vector


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def run_update_user_vector_test(user_vector, papers):
    """
    Runs a test of the update_user_vector function by simulating user feedback on paper recommendations.

    This function:
    - Embeds the provided papers (title + abstract) and computes initial cosine similarities to the user vector.
    - Applies hardcoded ratings.
    - Updates the user vector sequentially based on the ratings and paper embeddings.
    - Prints initial similarities, applied ratings, and updated similarities for all papers.

    Args:
        user_vector (List[float]): The current user embedding vector.
        papers (List[Dict]): A list of paper metadata dictionaries, each with at least 'title' and 'abstract' keys.

    Returns:
        None
    """
    print("\nRunning update_user_vector test...")

    paper_vectors = {}
    initial_sims = []

    # Compute initial similarities
    for i, paper in enumerate(papers):
        title = paper.get("title", f"Paper {i + 1}")
        abstract = paper.get("abstract", "")
        paper_vector = embed_papers(title, abstract)
        paper_vectors[title] = paper_vector

        assert isinstance(paper_vector, (list, np.ndarray))
        assert np.all(np.isfinite(paper_vector)), "Paper embedding contains invalid values"

        sim = cosine_similarity(user_vector, paper_vector)
        assert -1.0001 <= sim <= 1.0001, "Cosine similarity out of expected range"

        initial_sims.append((title, sim))
        print(f"{i + 1}. {title} - Initial Similarity: {sim:.4f}")

    # Hardcoded ratings
    paper_ratings = {}
    for i, (title, _) in enumerate(initial_sims):
        if i == 0:
            paper_ratings[title] = 5
        elif i == 1:
            paper_ratings[title] = 1
        elif i == 2:
            paper_ratings[title] = 1
        else:
            paper_ratings[title] = 5

    # Apply updates
    updated_vector = user_vector.copy()
    for title, rating in paper_ratings.items():
        updated_vector = update_user_vector(
            updated_vector, paper_vectors[title], rating
        )
        print(f"Applied rating {rating} to '{title}'")

    assert not np.allclose(updated_vector, user_vector), "User vector should change after updates"

    # Get new similarities
    print("\nUpdated similarities:")
    for title, paper_vector in paper_vectors.items():
        sim = cosine_similarity(updated_vector, paper_vector)
        assert -1.0001 <= sim <= 1.0001, "Updated cosine similarity out of expected range"

        # Ensure similarity changed at least slightly
        old_sim = dict(initial_sims)[title]
        assert not np.isclose(sim, old_sim), f"Similarity for '{title}' did not change"

        print(f"{title} - Updated Similarity: {sim:.4f}")


def test_update_user_vector_flow():
    user_vector = [0.1] * 1536

    test_papers = [
        {
            "title": "Deep Learning for Computer Vision",
            "abstract": "This paper presents novel deep learning approaches for computer vision tasks "
                        "including image classification and object detection.",
            "rating": 1,
        },
        {
            "title": "Natural Language Processing with Transformers",
            "abstract": "This paper explores transformer architectures for natural language processing tasks "
                        "including text generation and translation.",
            "rating": 5,
        },
        {
            "title": "Reinforcement Learning in Robotics",
            "abstract": "This paper discusses reinforcement learning applications in robotics for autonomous "
                        "navigation and manipulation.",
            "rating": 1,
        },
    ]

    run_update_user_vector_test(user_vector, test_papers)
