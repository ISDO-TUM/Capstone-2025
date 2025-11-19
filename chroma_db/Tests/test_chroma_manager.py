from unittest.mock import MagicMock, patch
import chromadb


@patch("chromadb.HttpClient")
def test_chromadb_list_collections(mock_client_cls):
    """
    Test that the ChromaDB client correctly lists collections
    and allows to access them. Uses mocks to avoid calling the real server.
    """

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_collection_1 = MagicMock()
    mock_collection_1.name = "test-collection-1"
    mock_collection_2 = MagicMock()
    mock_collection_2.name = "test-collection-2"

    mock_client.list_collections.return_value = [mock_collection_1, mock_collection_2]

    client = chromadb.HttpClient(host="localhost", port=8000)
    collections = client.list_collections()

    assert len(collections) == 2
    assert collections[0].name == "test-collection-1"
    assert collections[1].name == "test-collection-2"

    for coll in collections:
        client.get_collection(coll.name)
        client.get_collection.assert_called_with(coll.name)
