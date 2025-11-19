import pytest
import chromadb


@pytest.fixture
def collection():
    # for the local or end-to-end testing with docker, requires ChromeDB running
    # client = chromadb.HttpClient(host="localhost", port=8000)

    # in-memory client for the CI pipeline
    client = chromadb.Client()
    return client.get_or_create_collection("research-papers-test")


def test_query_returns_documents(collection):
    """
    This test checks that a ChromaDB query returns documents. It adds two mock documents
    to a test collection, runs a semantic query, and asserts that the response contains
    at least one returned document.
    """

    collection.add(
        documents=[
            "Climate change effects on Brazilian agriculture",
            "Impact of global warming on the Amazon rainforest",
        ],
        ids=["doc1", "doc2"],
    )

    query = "provide papers about climate change impacts in Brazil"

    results = collection.query(
        query_texts=[query],
        n_results=5,
    )

    assert "documents" in results
    assert len(results["documents"]) > 0
    assert len(results["documents"][0]) > 0
