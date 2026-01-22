# Tests

This directory contains all tests for the Capstone project.

## Structure

```
tests/
├── unit/               # Unit tests (organized by module)
│   ├── paper_handling/ # OpenAlex API and paper processing tests
│   ├── chroma_db/      # Vector database operation tests
│   └── llm/            # LLM, embeddings, and agent tests
└── e2e/                # End-to-end tests with Playwright
```

## Running Tests

### Run All Tests
```bash
uv run pytest tests/ -v
```

### Run Only Unit Tests
```bash
uv run pytest tests/unit -v
```

### Run Only E2E Tests
```bash
# Requires Docker services running with TEST_MODE=true
TEST_MODE=true docker compose up -d --build
uv run pytest tests/e2e -v
```

### Run Tests for a Specific Module
```bash
# Paper handling
uv run pytest tests/unit/paper_handling -v

# ChromaDB
uv run pytest tests/unit/chroma_db -v

# LLM
uv run pytest tests/unit/llm -v
```

## Documentation

- [Unit Tests Guide](unit/README.md) - Overview of all unit tests
- [E2E Tests Guide](e2e/README.md) - Guide for end-to-end testing with Playwright
- [Paper Handling Tests](unit/paper_handling/README.md) - OpenAlex API tests
- [ChromaDB Tests](unit/chroma_db/README.md) - Vector database tests
- [LLM Tests](unit/llm/README.md) - LLM and agent tests

## Test Statistics

Current test count:
- **Unit Tests**: 11 tests across 3 modules
- **E2E Tests**: 5 test files covering user flows

All tests use pytest and can be run with `uv run pytest`.

## CI/CD

Tests are automatically run in GitHub Actions:
1. **Lint & Format** - Code quality checks with ruff
2. **Unit Tests** - Fast unit tests (no Docker required)
3. **E2E Tests** - Full integration tests (requires Docker)
4. **Deploy** - Deployment to production (main branch only)

See `.github/workflows/ci.yml` for the complete CI pipeline.
