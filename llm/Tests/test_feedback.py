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

        sim = cosine_similarity(user_vector, paper_vector)
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
        updated_vector = update_user_vector(updated_vector, paper_vectors[title], rating)
        print(f"Applied rating {rating} to '{title}'")

    # Get new similarities
    print("\nUpdated similarities:")
    for title, paper_vector in paper_vectors.items():
        sim = cosine_similarity(updated_vector, paper_vector)
        print(f"{title} - Updated Similarity: {sim:.4f}")
