from paper_ranking.paper_ranker import get_best_papers
from llm.Embeddings import embed_user_profile, embed_papers
from chroma_db.chroma_vector_db import chroma_db
from paper_handling.database_handler import get_papers_by_hash
from typing import List


def update_user_vector(user_vector: List[float], paper_vector: List[float], rating: int) -> List[float]:
    weight = (rating - 3) * 0.05
    updated_vector = [
        u + weight * p
        for u, p in zip(user_vector, paper_vector)
    ]
    return updated_vector


def test_recommendation_with_feedback(user_profile: str, rating: int = 5):
    # Step 1: Get initial paper recommendations
    print(f"User profile input: {user_profile}")
    initial_papers = get_best_papers(user_profile)
    if not initial_papers:
        print("No initial papers found. Aborting test.")
        return

    print("\nInitial Recommendations:")
    for i, p in enumerate(initial_papers):
        print(f"{i + 1}. {p.get('title', 'No Title')}")

    # Step 2: Embed the user profile
    user_vector = embed_user_profile(user_profile)

    # Step 3: Embed first paper and simulate rating feedback
    first_paper = initial_papers[0]
    title = first_paper.get('title', '')
    abstract = first_paper.get('abstract', '')  # Adjust if your data uses another key or is missing

    paper_vector = embed_papers(title, abstract)

    print(f"\nGiving rating {rating} to paper: {title}")

    # Step 4: Update user vector based on feedback
    updated_user_vector = update_user_vector(user_vector, paper_vector, rating)

    # Step 5: Get new recommendations based on updated user vector
    updated_hashes = chroma_db.perform_similarity_search(10, updated_user_vector)
    updated_papers = get_papers_by_hash(updated_hashes)

    print("\nUpdated Recommendations After Feedback:")
    for i, p in enumerate(updated_papers):
        print(f"{i + 1}. {p.get('title', 'No Title')}")


if __name__ == "__main__":
    # Example usage:
    test_recommendation_with_feedback("graph neural networks for drug discovery", rating=5)
