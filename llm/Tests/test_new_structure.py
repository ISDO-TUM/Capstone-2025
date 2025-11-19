import requests

# Base URL for the Flask app
BASE_URL = "http://localhost:7500"


def test_user_profile_embeddings():
    print("Testing User Profile Embedding Functionality:")

    # create a project
    project_data = {
        "title": "AI Research Project",
        "prompt": "Research on machine learning applications in healthcare",
    }

    response = requests.post(
        f"{BASE_URL}/api/createProject", json=project_data, timeout=10
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
        f"{BASE_URL}/api/user-profile/create-embedding",
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
        f"{BASE_URL}/api/createProject", json=project_data2, timeout=10
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
        f"{BASE_URL}/api/user-profile/create-embedding",
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
        f"{BASE_URL}/api/user-profile/find-similar", json=similar_data, timeout=10
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
        f"{BASE_URL}/api/user-profile/similarity-matrix", timeout=10
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
