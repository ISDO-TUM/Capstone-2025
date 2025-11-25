from unittest.mock import patch
import requests
import json


@patch("requests.post")
@patch("requests.get")
def test_user_profile_embeddings(mock_get, mock_post):

    def post_side_effect(url, *args, **kwargs):
        if url.endswith("/api/createProject"):
            return make_response({"project_id": 999})

        if url.endswith("/api/user-profile/create-embedding"):
            return make_response({"embedding_length": 1536})

        if url.endswith("/api/user-profile/find-similar"):
            return make_response({
                "similar_projects": [
                    {"project_id": 1001, "similarity_score": 0.91},
                    {"project_id": 1002, "similarity_score": 0.87},
                ]
            })

        raise RuntimeError(f"Unexpected POST URL: {url}")

    def get_side_effect(url, *args, **kwargs):
        if url.endswith("/api/user-profile/similarity-matrix"):
            return make_response({
                "projects": [
                    {"project_id": 999, "title": "AI Research Project"},
                    {"project_id": 1001, "title": "Healthcare AI Project"},
                ]
            })

        raise RuntimeError(f"Unexpected GET URL: {url}")

    def make_response(data: dict):
        r = requests.Response()
        r.status_code = 200
        r._content = json.dumps(data).encode("utf-8")
        return r

    mock_post.side_effect = post_side_effect
    mock_get.side_effect = get_side_effect

    print("Testing User Profile Embedding Functionality:")

    # create a project
    project_data = {
        "title": "AI Research Project",
        "prompt": "Research on machine learning applications in healthcare",
    }

    response = requests.post(
        "http://localhost:7500/api/createProject",
        json=project_data,
    )
    assert response.status_code == 200, f"Failed to create project: {response.text}"
    project_id = response.json()["project_id"]
    print(f"Project created with ID: {project_id}")

    # Create user profile embedding
    user_profile_data = {
        "project_id": project_id,
        "user_profile_text": "I am a researcher interested in machine learning, deep learning, and healthcare "
        "applications. I work on computer vision for medical imaging and natural language "
        "processing for clinical text analysis.",
    }

    response = requests.post(
        "http://localhost:7500/api/user-profile/create-embedding",
        json=user_profile_data,
        timeout=10,
    )
    assert response.status_code == 200, f"Failed to create embedding: {response.text}"
    result = response.json()
    print(f"Embedding created successfully. Length: {result['embedding_length']}")

    # Create another project with similar profile
    project_data2 = {
        "title": "Healthcare AI Project",
        "prompt": "Deep learning for medical diagnosis",
    }

    response = requests.post(
        "http://localhost:7500/api/createProject", json=project_data2, timeout=10
    )
    assert response.status_code == 200, (
        f"Failed to create second project: {response.text}"
    )
    project_id2 = response.json()["project_id"]
    print(f"Second project created with ID: {project_id2}")

    # Create similar user profile embedding
    user_profile_data2 = {
        "project_id": project_id2,
        "user_profile_text": "I am a medical AI researcher focusing on deep learning for healthcare. I specialize in "
        "computer vision for radiology and clinical decision support systems.",
    }

    response = requests.post(
        "http://localhost:7500/api/user-profile/create-embedding",
        json=user_profile_data2,
        timeout=10,
    )
    assert response.status_code == 200, (
        f"Failed to create second embedding: {response.text}"
    )
    result = response.json()
    print(
        f"Second embedding created successfully. Length: {result['embedding_length']}"
    )

    # Find similar user profiles
    similar_data = {"project_id": project_id, "limit": 3}

    response = requests.post(
        "http://localhost:7500/api/user-profile/find-similar", json=similar_data, timeout=10
    )
    assert response.status_code == 200, (
        f"Failed to find similar profiles: {response.text}"
    )

    result = response.json()
    similar_projects = result["similar_projects"]
    print(f"Found {len(similar_projects)} similar projects:")
    for i, project in enumerate(similar_projects, 1):
        print(
            f"{i}. Project ID: {project['project_id']}, Similarity Score: {project['similarity_score']:.4f}"
        )

    # Get similarity matrix
    response = requests.get(
        "http://localhost:7500/api/user-profile/similarity-matrix", timeout=10
    )
    assert response.status_code == 200, (
        f"Failed to get similarity matrix: {response.text}"
    )

    result = response.json()
    projects = result["projects"]
    print(f"Found {len(projects)} projects with embeddings:")
    for project in projects:
        print(f"Project ID: {project['project_id']}, Title: {project['title']}")

    print("Test completed!")
