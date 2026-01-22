# LLM Unit Tests

Unit tests for the LLM module, including embeddings, agent tools and quality control.

## Test Files

- **test_new_structure.py** - Tests for user profile embeddings
- **test_tooling.py** - Tests for agent tools (scope detection, QC, filters)
- **embedding_learning_test.py** - Tests for embedding learning algorithms
- **user_profile_embeddings_test.py** - Tests for user profile embedding creation
- **conftest.py** - Shared fixtures and configuration

## What's Tested

### User Profile Embeddings
- Creating embeddings from project descriptions
- Storing and retrieving profile embeddings
- Embedding dimension validation (1536-d vectors)

### Agent Tools
- **Scope Detection**: Identifying out-of-scope queries
- **Keyword Extraction**: Extracting keywords from user queries
- **Quality Control**: Deciding if queries need reformulation
- **Filter Detection**: Identifying filter instructions in queries
- **Complete Workflow**: End-to-end agent tooling pipeline

### Embedding Learning
- Learning from user interactions
- Adjusting embeddings based on feedback
- Profile refinement over time

## Running These Tests

```bash
# Run all LLM tests
uv run pytest tests/unit/llm -v

# Run specific test file
uv run pytest tests/unit/llm/test_tooling.py -v

# Run specific test with mock mode
uv run pytest tests/unit/llm/test_tooling.py::test_scope_detection -v
```

## Test Modes

Tests support a `mock` mode (via `conftest.py`) that uses:
- MockLLM for deterministic responses
- No real OpenAI API calls
- Fast test execution

## Dependencies

These tests use:
- `pytest` for test framework
- `numpy` for vector operations
- `llm.Embeddings` for embedding generation
- `llm.LLMDefinition` for LLM instances
- Mock fixtures from `conftest.py`

## Notes

- Tests run in `TEST_MODE=true` to avoid real API calls
- Mock LLM provides deterministic responses for reliable testing
- All embedding tests verify 1536-dimensional vectors (OpenAI text-embedding-3-small)
