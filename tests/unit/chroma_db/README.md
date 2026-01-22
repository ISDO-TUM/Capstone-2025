# ChromaDB Unit Tests

Unit tests for the ChromaDB vector database operations, including storage, retrieval, and similarity search.

## Test Files

- **test_chroma_manager.py** - Tests for collection management and client operations
- **test_chroma_paper_ingestion.py** - Tests for storing paper embeddings
- **test_chroma_query.py** - Tests for querying and similarity search

## What's Tested

### Collection Management
- Listing ChromaDB collections
- Creating and accessing collections
- Client connection handling

### Paper Ingestion
- Storing paper embeddings in ChromaDB
- Handling embedding vectors (1536 dimensions)
- Upserting papers with hash-based IDs

### Similarity Search
- Querying ChromaDB with user profile embeddings
- Retrieving top-k similar papers
- Cosine similarity scoring

## Running These Tests

```bash
# Run all ChromaDB tests
uv run pytest tests/unit/chroma_db -v

# Run specific test file
uv run pytest tests/unit/chroma_db/test_chroma_manager.py -v
uv run pytest tests/unit/chroma_db/test_chroma_paper_ingestion.py -v
uv run pytest tests/unit/chroma_db/test_chroma_query.py -v
```

## Dependencies

These tests use:
- `pytest` for test framework
- `unittest.mock` for mocking ChromaDB HTTP client
- `chromadb` library
- `chroma_db.chroma_vector_db` module being tested

## Notes

Tests use mocked ChromaDB clients to avoid requiring a running ChromaDB instance during testing.
