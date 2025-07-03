import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.projects_database_handler import (
    add_new_project_to_db,
    add_user_profile_embedding,
    get_user_profile_embedding,
    get_project_data
)
from llm.Embeddings import embed_user_profile
from llm.tools.paper_ranker import get_best_papers


def test_embedding_storage_and_retrieval():
    project_id = add_new_project_to_db(
        "Test AI Research Project",
        "Research on machine learning applications in healthcare"
    )

    user_profile_text = (
        "I am a researcher interested in machine learning, deep learning, and healthcare applications."
    )
    embedding = embed_user_profile(user_profile_text)
    add_user_profile_embedding(project_id, embedding)

    retrieved_embedding = get_user_profile_embedding(project_id)
    if retrieved_embedding is None:
        return False

    if embedding == retrieved_embedding:
        return True
    else:
        return False


def test_embedding_update():
    project_id = add_new_project_to_db(
        "Test Update Project",
        "Testing embedding updates"
    )

    initial_embedding = embed_user_profile("I am interested in quantum computing")
    add_user_profile_embedding(project_id, initial_embedding)

    updated_embedding = embed_user_profile(
        "I am interested in quantum computing and machine learning for drug discovery"
    )
    add_user_profile_embedding(project_id, updated_embedding)

    retrieved_embedding = get_user_profile_embedding(project_id)
    return retrieved_embedding == updated_embedding


def test_get_best_papers_with_text():
    user_profile_text = "machine learning for healthcare applications"
    try:
        papers = get_best_papers(user_profile_text)
        return bool(papers)
    except Exception:
        return False


def test_get_best_papers_with_project_id():
    project_id = add_new_project_to_db(
        "Test Project for get_best_papers",
        "Testing get_best_papers with project ID"
    )
    embedding = embed_user_profile("deep learning for medical image analysis")
    add_user_profile_embedding(project_id, embedding)

    try:
        papers = get_best_papers(project_id)
        return bool(papers)
    except Exception:
        return False


def test_get_best_papers_fallback():
    project_id = add_new_project_to_db(
        "Test Project Without Embedding",
        "Testing fallback behavior"
    )

    if get_user_profile_embedding(project_id) is not None:
        return False

    try:
        papers = get_best_papers(project_id)
        return bool(papers)
    except Exception:
        return False


def test_database_integrity():
    project_id = add_new_project_to_db(
        "Database Integrity Test",
        "Testing database integrity"
    )
    embedding = embed_user_profile("artificial intelligence for robotics")
    add_user_profile_embedding(project_id, embedding)

    project_data = get_project_data(project_id)
    if project_data is None:
        return False

    stored_embedding_raw = project_data.get("user_profile_embedding")
    if stored_embedding_raw is None:
        return False

    if isinstance(stored_embedding_raw, str):
        stored_embedding = json.loads(stored_embedding_raw)
    elif isinstance(stored_embedding_raw, list):
        stored_embedding = stored_embedding_raw
    else:
        return False

    return len(stored_embedding) == len(embedding)


def run_all_tests():
    tests = [
        ("Basic Storage and Retrieval", test_embedding_storage_and_retrieval),
        ("Embedding Update", test_embedding_update),
        ("get_best_papers with Text", test_get_best_papers_with_text),
        ("get_best_papers with Project ID", test_get_best_papers_with_project_id),
        ("get_best_papers Fallback", test_get_best_papers_fallback),
        ("Database Integrity", test_database_integrity),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception:
            results.append((test_name, False))

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    print(f"\n{passed}/{total} tests passed")
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
