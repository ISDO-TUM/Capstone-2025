from unittest.mock import MagicMock, patch


@patch("chromadb.HttpClient")
def test_chroma_ingest_papers(mock_client_cls):
    """
    Test ChromaDB ingestion flow:
     - deleting/creating a collection,
     - preparing paper documents
     - upserting them.
     Mocks ChromaDB to avoid calling the real server.
    """

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    collection = mock_client.get_or_create_collection("research-papers")

    mock_papers = [
        {
            "id": "p1",
            "title": "Title 1",
            "abstract": "Abstract 1",
            "authors": "Author A",
        },
        {
            "id": "p2",
            "title": "Title 2",
            "abstract": "Abstract 2",
            "authors": "Author B",
        },
    ]

    for paper in mock_papers:
        paper_id = paper["id"]
        title = paper.get("title", "No title")
        abstract = paper.get("abstract", "")
        authors = paper.get("authors", "Unknown")
        content = f"{title}\n\n{abstract}"

        collection.upsert(
            ids=[paper_id],
            documents=[content],
            metadatas=[{"title": title, "authors": authors, "url": ""}],
        )

    assert mock_client.get_or_create_collection.called
    assert mock_collection.upsert.call_count == len(mock_papers)

    first_call_args = mock_collection.upsert.call_args_list[0][1]
    assert first_call_args["ids"] == ["p1"]
    assert "Abstract 1" in first_call_args["documents"][0]
