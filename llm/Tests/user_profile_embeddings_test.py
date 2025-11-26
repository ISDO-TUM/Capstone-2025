from llm.tools.paper_ranker import get_best_papers
from llm.Embeddings import embed_user_profile
from database.projects_database_handler import (
    add_new_project_to_db,
    add_user_profile_embedding,
    get_user_profile_embedding,
    get_project_data,
)
import sys
import os
import json
import pytest
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(autouse=True)
def mock_request_and_db():
    with (
        patch("database.projects_database_handler.request") as mock_request,
        patch(
            "database.projects_database_handler.add_new_project_to_db", return_value=1
        ),
        patch(
            "database.projects_database_handler.add_user_profile_embedding",
            return_value=True,
        ),
        patch(
            "database.projects_database_handler.get_user_profile_embedding",
            return_value=[0.5] * 10,
        ),
    ):
        mock_request.auth = True
        yield


@pytest.fixture(autouse=True)
def mock_get_best_papers(monkeypatch):
    # Return dummy papers for testing
    monkeypatch.setattr(
        "llm.user_profile_embeddings.get_best_papers",
        lambda text, project_id=None: [{"title": "Dummy Paper", "score": 0.9}],
    )


def test_embedding_storage_and_retrieval():
    project_id = add_new_project_to_db(
        "Test AI Research Project",
        "Research on machine learning applications in healthcare",
    )

    user_profile_text = (
        "I am a researcher interested in machine learning, deep learning, "
        "and healthcare applications."
    )
    embedding = embed_user_profile(user_profile_text)
    add_user_profile_embedding(project_id, embedding)

    retrieved_embedding = get_user_profile_embedding(project_id)

    assert retrieved_embedding is not None
    assert embedding == retrieved_embedding


def test_embedding_update():
    project_id = add_new_project_to_db(
        "Test Update Project", "Testing embedding updates"
    )

    initial_embedding = embed_user_profile("I am interested in quantum computing")
    add_user_profile_embedding(project_id, initial_embedding)

    updated_embedding = embed_user_profile(
        "I am interested in quantum computing and machine learning for drug discovery"
    )
    add_user_profile_embedding(project_id, updated_embedding)

    retrieved_embedding = get_user_profile_embedding(project_id)

    assert retrieved_embedding == updated_embedding


def test_get_best_papers_with_text():
    user_profile_text = "machine learning for healthcare applications"
    papers = get_best_papers(user_profile_text)

    assert papers  # checks not empty / not None


def test_get_best_papers_with_project_id():
    project_id = add_new_project_to_db(
        "Test Project for get_best_papers",
        "Testing get_best_papers with project ID",
    )
    embedding = embed_user_profile("deep learning for medical image analysis")
    add_user_profile_embedding(project_id, embedding)

    papers = get_best_papers(project_id)
    assert papers


def test_get_best_papers_fallback():
    project_id = add_new_project_to_db(
        "Test Project Without Embedding",
        "Testing fallback behavior",
    )

    # Ensure no embedding exists
    assert get_user_profile_embedding(project_id) is None

    papers = get_best_papers(project_id)
    assert papers


def test_database_integrity():
    project_id = add_new_project_to_db(
        "Database Integrity Test",
        "Testing database integrity",
    )
    embedding = embed_user_profile("artificial intelligence for robotics")
    add_user_profile_embedding(project_id, embedding)

    project_data = get_project_data(project_id)
    assert project_data is not None

    stored_embedding_raw = project_data.get("user_profile_embedding")
    assert stored_embedding_raw is not None

    if isinstance(stored_embedding_raw, str):
        stored_embedding = json.loads(stored_embedding_raw)
    else:
        stored_embedding = stored_embedding_raw

    assert isinstance(stored_embedding, list)
    assert len(stored_embedding) == len(embedding)
