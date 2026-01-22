# Unit Tests

This directory contains all unit tests for the Capstone project, organized by module.

## Structure

```
tests/unit/
├── paper_handling/     # Tests for OpenAlex API and paper processing
├── chroma_db/          # Tests for ChromaDB vector database operations
└── llm/                # Tests for LLM, embeddings, and agent functionality
```

## Running Unit Tests

Run all unit tests:
```bash
uv run pytest tests/unit -v
```

Run tests for a specific module:
```bash
# Paper handling tests
uv run pytest tests/unit/paper_handling -v

# ChromaDB tests
uv run pytest tests/unit/chroma_db -v

# LLM tests
uv run pytest tests/unit/llm -v
```

## Test Coverage

- **paper_handling**: Tests for fetching papers from OpenAlex API
- **chroma_db**: Tests for vector storage, similarity search, and collection management
- **llm**: Tests for embeddings, feedback loops, agent tools, and quality control

## Test Count

Currently **11 unit tests** across all modules.
