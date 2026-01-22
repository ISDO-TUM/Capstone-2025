# Paper Handling Unit Tests

Unit tests for the paper handling module, which manages fetching and processing academic papers from OpenAlex.

## Test Files

- **test_paper_handling.py** - Tests for OpenAlex API integration and paper fetching

## What's Tested

### OpenAlex API Integration
- Fetching papers from multiple search queries
- Handling API responses and parsing paper metadata
- Mock testing to avoid real API calls during tests

## Running These Tests

```bash
# Run all paper handling tests
uv run pytest tests/unit/paper_handling -v

# Run specific test
uv run pytest tests/unit/paper_handling/test_paper_handling.py::test_fetch_works_multiple_queries_multiple_results -v
```

## Dependencies

These tests use:
- `pytest` for test framework
- `unittest.mock` for mocking OpenAlex API calls
- `paper_handling.paper_handler` module being tested
