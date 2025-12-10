# E2E Testing Guide

This directory contains end-to-end tests for the Capstone-2025 application using Playwright and Pytest.

## Quick Start

### Automated Testing (Recommended)

**E2E tests run automatically in the CI/CD pipeline** on:
- Pull requests to `main` or `develop` branches
- Pushes to `main` branch

View test results in the GitHub Actions tab. This is the recommended approach as all services are properly configured.

### Running Tests Locally

#### Prerequisites
- **PostgreSQL** (port 5432)
- **ChromaDB** (port 8000)
- **Playwright** and **Pytest** installed
- **uv** and virtual environment set up

#### Using the Test Script (Recommended)

**Always use `./run_tests.sh` instead of `uv run pytest`** to avoid environment corruption:

```bash
# From project root, run all E2E tests
./run_tests.sh tests/e2e -v

# Run specific test file
./run_tests.sh tests/e2e/test_basic.py -v

# Run specific test
./run_tests.sh tests/e2e/test_basic.py::test_homepage_loads -v

# Run unit tests separately
./run_tests.sh llm/Tests chroma_db/Tests paper_handling -v
```

**Why use `./run_tests.sh` instead of `uv run pytest`?**

`uv run pytest` has a known bug where it constantly recreates the virtual environment due to symlink validation issues, causing:
- Tests to fail unpredictably on subsequent runs
- Environment corruption with wrong platform binaries
- Wasted time recreating `.venv` on every execution

The `./run_tests.sh` script uses direct venv activation (`source .venv/bin/activate`) which bypasses this bug and provides stable test execution.

**Important:** Do not run unit tests and E2E tests together (e.g., `./run_tests.sh .`). They have conflicting fixture requirements:
- Unit tests mock ChromaDB globally
- E2E tests require real ChromaDB connections

Always run them separately as shown above.

#### Setup Environment

```bash
# Install dependencies (from project root)
uv sync
playwright install chromium

# Start required services
docker compose up -d db chromadb

# Wait for services to start
sleep 5
```

## Test Coverage

The E2E test suite covers:

### 1. Basic Functionality (`test_basic.py`)
- Homepage loads correctly
- Create project page loads
- Basic project creation flow

### 2. Recommendations Flow (`test_recommendations.py`)
- Complete project creation → recommendations workflow
- Paper metadata display (authors, year, venue, citations, FWCI, percentile)
- PDF button and Open Access badge rendering
- "Read Paper" link positioning
- Search and filter functionality
- SSE connection establishment
- Paper count validation

### 3. Paper Rating (`test_paper_rating.py`)
- Rating papers with 1-5 stars
- Low rating (1-2 stars) triggers replacement
- Rating persistence after page reload
- Multiple paper ratings
- Notification on replacement
- UI updates on rating
- Cannot rate replaced papers

### 4. Load More Papers (`test_load_more.py`)
- Load More button exists and works
- Clicking Load More increases paper count
- Metadata consistency between initial and loaded papers
- Authors, year, venue display in loaded papers
- Citation metrics (citations, FWCI, percentile) in loaded papers
- Load More button disabled when no more papers available

## Test Structure

```
tests/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures and configuration
│   ├── screenshots/             # Failure screenshots (auto-generated)
│   ├── test_basic.py            # Basic navigation tests
│   ├── test_recommendations.py  # Full recommendation flow
│   ├── test_paper_rating.py     # Rating and replacement tests
│   └── test_load_more.py        # Load More functionality
└── README.md                    # This file
```

## Running Specific Tests

All commands should be run from the project root using `./run_tests.sh`:

### Run All E2E Tests
```bash
./run_tests.sh tests/e2e
```

### Run Specific Test File
```bash
./run_tests.sh tests/e2e/test_basic.py -v
```

### Run Specific Test Class
```bash
./run_tests.sh tests/e2e/test_recommendations.py::TestRecommendationsFlow -v
```

### Run Single Test
```bash
./run_tests.sh tests/e2e/test_basic.py::test_homepage_loads -v
```

### Run with Verbose Output
```bash
./run_tests.sh tests/e2e -vv
```

## Debugging

### View Browser During Tests
```bash
./run_tests.sh tests/e2e --headed
```

### Slow Down Execution
```bash
./run_tests.sh tests/e2e --headed --slowmo=1000
```

### Run Single Test with Debugging
```bash
./run_tests.sh tests/e2e/test_load_more.py::TestLoadMorePapers::test_load_more_button_exists_and_increases_count -v
```

### View Screenshots
Failed tests automatically save screenshots to `tests/e2e/screenshots/`.

### Pytest Debugging Options
```bash
./run_tests.sh tests/e2e -v -s          # Show print statements
./run_tests.sh tests/e2e -v --pdb       # Drop into debugger on failure
./run_tests.sh tests/e2e -v --maxfail=1 # Stop after first failure
```

## Mock LLM

Tests use a **Mock LLM** (defined in `mock_llm.py`) instead of real OpenAI API calls:

**Benefits:**
- ✅ **Zero cost** - No API charges
- ✅ **Deterministic** - Same responses every time
- ✅ **Fast** - No network latency
- ✅ **Offline** - Works without internet
- ✅ **No rate limits** - Run tests infinitely

**Customization:**
Edit `tests/e2e/mock_llm.py` to modify mock responses for different scenarios.

## Important Notes

- **Mock LLM**: All tests use mocked LLM responses (no real API calls)
- **SSE Streams**: Generous timeouts (90s) used for recommendation loading
- **Test Independence**: Each test gets a fresh browser page and database state
- **Async Operations**: Appropriate waits for rating/replacement (10s+)
- **Screenshots**: Automatically captured on test failure in `tests/e2e/screenshots/`
- **Serial Execution**: Tests run one at a time to avoid database conflicts

## Fixtures

### `flask_server` (session scope)
Starts Flask app on port 5556 for testing.

### `page` (function scope)
Provides fresh Playwright Page for each test with:
- Viewport: 1920x1080
- Console logging enabled
- Error logging enabled
- Screenshot capture on failure

### `test_project_data`
Sample project data with name, description, deadline, and paper count.

### `enable_test_mode` (session scope, autouse)
Automatically enables TEST_MODE and Mock LLM:
- Replaces real LLM with Mock LLM (zero API calls, deterministic responses)
- Sets database connection parameters
- Configures ChromaDB host

## Troubleshooting

### ChromaDB Connection Error
```
ValueError: Could not connect to a Chroma server
```
**Solution**:
```bash
# Start ChromaDB
docker compose up -d chromadb
# OR set environment variable
export CHROMA_HOST=localhost
```

### PostgreSQL Connection Error
```
connection to server failed: fe_sendauth: no password supplied
```
**Solution**:
```bash
# Start PostgreSQL
docker compose up -d db
# OR set environment variables
export DB_HOST=127.0.0.1
export DB_NAME=papers
export DB_USER=user
export DB_PASSWORD=password
export DB_PORT=5432
```

### Playwright Not Found
```
ModuleNotFoundError: No module named 'playwright'
```
**Solution**:
```bash
pip install pytest pytest-playwright
playwright install chromium
```

### Test Timeout Issues
If tests are timing out:
- Check that ChromaDB and PostgreSQL are running
- Verify OpenAI API key is set correctly
- Increase timeouts in test files if needed (currently 90s for LLM operations)

## CI/CD

Tests are automatically run in GitHub Actions on pull requests and main branch pushes.

The workflow:
1. Sets up PostgreSQL service container
2. Installs Python dependencies
3. Installs Playwright browsers
4. Runs pytest with all E2E tests
5. Uploads screenshots as artifacts on failure

View workflow configuration in `.github/workflows/e2e-tests.yml`.

## Best Practices

- **Use `./run_tests.sh`**: Always use the test script instead of `uv run pytest` to avoid environment corruption
- **Separate Test Suites**: Never run unit tests and E2E tests together - they have conflicting fixture requirements
- **Run in CI**: Let GitHub Actions handle full test runs automatically
- **Debug Locally**: Run specific tests with `--headed` flag for visual debugging
- **Check Screenshots**: Review failure screenshots in `tests/e2e/screenshots/` for debugging
- **Serial Execution**: Tests run one at a time by default (no parallel execution)
