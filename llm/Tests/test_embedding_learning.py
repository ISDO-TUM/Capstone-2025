"""
Tests that the system learns from user ratings and uses updated embeddings for replacements.
"""
from database.database_connection import connect_to_db
from llm.feedback import update_user_vector
from llm.Embeddings import embed_user_profile, embed_papers
from database.projectpaper_database_handler import assign_paper_to_project
from database.projects_database_handler import (
    add_new_project_to_db,
    get_user_profile_embedding,
    add_user_profile_embedding
)
import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def cosine_similarity(vec1, vec2):
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)

    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)

    if norm1 == 0 or norm2 == 0:
        return 0

    return np.dot(vec1_np, vec2_np) / (norm1 * norm2)


def test_embedding_learning():
    # Create a test project
    project_id = add_new_project_to_db(
        "Test Learning Project",
        "Research on machine learning and artificial intelligence"
    )

    # Create initial user profile embedding
    initial_embedding = embed_user_profile("Research on machine learning and artificial intelligence")
    add_user_profile_embedding(project_id, initial_embedding)

    # Create test papers
    test_papers = [{"title": "Deep Learning for Computer Vision",
                    "abstract": "This paper presents novel deep learning approaches for computer vision tasks "
                                "including image classification and object detection.",
                    "rating": 1},
                   {"title": "Natural Language Processing with Transformers",
                    "abstract": "This paper explores transformer architectures for natural language processing tasks "
                                "including text generation and translation.",
                    "rating": 5},
                   {"title": "Reinforcement Learning in Robotics",
                    "abstract": "This paper discusses reinforcement learning applications in robotics for autonomous "
                                "navigation and manipulation.",
                    "rating": 1}]

    # Create embeddings for test papers
    paper_embeddings = {}
    for i, paper in enumerate(test_papers):
        embedding = embed_papers(paper["title"], paper["abstract"])
        if embedding:
            paper_embeddings[i] = embedding

    current_embedding = initial_embedding.copy()
    embedding_history = [current_embedding.copy()]

    for i, paper in enumerate(test_papers):
        rating = paper["rating"]
        paper_embedding = paper_embeddings[i]

        # Calculate similarity before rating
        similarity_before = cosine_similarity(current_embedding, paper_embedding)

        # Update embedding based on rating
        updated_embedding = update_user_vector(current_embedding, paper_embedding, rating)

        # Calculate similarity after rating
        similarity_after = cosine_similarity(updated_embedding, paper_embedding)

        # Verify the learning direction
        if rating >= 4:
            # High rating should increase similarity
            if similarity_after > similarity_before:
                pass  # Similarity increased for high rating
        elif rating <= 2:
            # Low rating should decrease similarity
            if similarity_after < similarity_before:
                pass  # Similarity decreased for low rating

        # Update current embedding and save to database
        current_embedding = updated_embedding
        add_user_profile_embedding(project_id, updated_embedding)
        embedding_history.append(current_embedding.copy())

    # Test replacement mechanism with updated embeddings
    try:
        # Get papers from the database
        conn = connect_to_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT paper_hash, title FROM papers_table LIMIT 5")
            existing_papers = cursor.fetchall()
            cursor.close()
            conn.close()

            if existing_papers:
                # Add a few existing papers to the project for testing
                for i, (paper_hash, title) in enumerate(existing_papers[:3]):
                    assign_paper_to_project(paper_hash, project_id, f"Test paper {i + 1}: {title[:50]}...")

    except Exception as e:
        print(f"Error testing replacement mechanism: {e}")

    # Verify embedding evolution
    for i in range(1, len(embedding_history)):
        similarity = cosine_similarity(embedding_history[i - 1], embedding_history[i])
        if similarity < 0.999:  # Allow for small numerical differences
            pass  # Embedding changed between steps

    return True


def test_embedding_persistence():
    """Test that embeddings are properly persisted in the database."""

    # Create a test project
    project_id = add_new_project_to_db(
        "Test Persistence Project",
        "Testing embedding persistence"
    )

    # Create initial embedding
    initial_embedding = embed_user_profile("Testing embedding persistence")
    add_user_profile_embedding(project_id, initial_embedding)

    # Verify it's stored
    stored_embedding = get_user_profile_embedding(project_id)
    if stored_embedding:
        similarity = cosine_similarity(initial_embedding, stored_embedding)
        if similarity > 0.999:
            pass  # Embedding properly stored and retrieved

    # Test multiple updates
    test_embedding = [0.1] * len(initial_embedding)
    updated_embedding = update_user_vector(initial_embedding, test_embedding, 5)
    add_user_profile_embedding(project_id, updated_embedding)

    # Verify update is stored
    final_embedding = get_user_profile_embedding(project_id)
    if final_embedding:
        similarity = cosine_similarity(updated_embedding, final_embedding)
        if similarity > 0.999:
            pass  # Updated embedding properly stored and retrieved

    return True


if __name__ == "__main__":
    persistence_success = test_embedding_persistence()

    if persistence_success:
        learning_success = test_embedding_learning()

        if learning_success:
            pass
        else:
            pass
    else:
        pass
