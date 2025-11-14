# E2E Testing Guide

This directory contains end-to-end tests for the Capstone-2025 application using Playwright and Pytest.

## Quick Start

### Automated Testing (Recommended)

**E2E tests run automatically in the CI/CD pipeline** on:
- Pull requests to `main` or `develop` branches
- Pushes to `main` branch

View test results in the GitHub Actions tab. This is the recommended approach as all services are properly configured.

### Running Tests Locally (Optional)

If you want to run tests locally for development/debugging:

#### Prerequisites
- **PostgreSQL** (port 5432)
- **ChromaDB** (port 8000)
- **Playwright** and **Pytest** installed

#### Option 1: Using the Helper Script (Easiest)

```bash
# Navigate to the e2e tests directory
cd tests/e2e/

# Run all tests
./run_e2e_tests.sh .

# Run specific test file
./run_e2e_tests.sh test_basic.py -v

# Run specific test
./run_e2e_tests.sh test_basic.py::TestBasic::test_homepage_loads -v

# Return to project root
cd ../..
```

#### Option 2: Using Docker Compose

```bash
# From project root, start required services
docker compose up -d db chromadb

# Wait for services to start
sleep 5

# Navigate to e2e tests directory and run tests
cd tests/e2e/
./run_e2e_tests.sh . -v
cd ../..
```

#### Option 3: Manual Setup

```bash
# Install dependencies (from project root)
pip install pytest pytest-playwright pytest-asyncio
playwright install chromium

# Set environment variables
export TEST_MODE=true
export CHROMA_HOST=localhost
export DB_HOST=127.0.0.1
export DB_NAME=papers
export DB_USER=user
export DB_PASSWORD=password
export DB_PORT=5432

# Navigate to e2e tests and run
cd tests/e2e/
pytest . -v
cd ../..
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

```bash
# Navigate to e2e tests directory
cd tests/e2e/

# Run all tests
./run_e2e_tests.sh .

# Run specific test file
./run_e2e_tests.sh test_basic.py -v

## Running Specific Tests

### Run All Tests in a File
```bash
cd tests/e2e/
./run_e2e_tests.sh test_basic.py
cd ../..
```

### Run a Specific Test Class
```bash
cd tests/e2e/
./run_e2e_tests.sh test_recommendations.py::TestRecommendationFlow
cd ../..
```

### Run a Single Test
```bash
cd tests/e2e/
./run_e2e_tests.sh test_basic.py::TestBasicFunctionality::test_can_visit_home
cd ../..
```

# Run with verbose output
./run_e2e_tests.sh . -v

# Run with extra verbose output
./run_e2e_tests.sh . -vv

# Return to project root
cd ../..
```

## Debugging

### View Browser During Tests
```bash
cd tests/e2e/
pytest . --headed
cd ../..
```

### Slow Down Execution
```bash
cd tests/e2e/
pytest . --headed --slowmo=1000
cd ../..
```

### Run Single Test
```bash
cd tests/e2e/
./run_e2e_tests.sh test_load_more.py::TestLoadMorePapers::test_load_more_button_works -v
cd ../..
```

### View Screenshots
Failed tests automatically save screenshots to `tests/e2e/screenshots/`.

### Pytest Debugging Options
```bash
cd tests/e2e/
pytest . -v -s          # Show print statements
pytest . -v --pdb       # Drop into debugger on failure
pytest . -v --maxfail=1 # Stop after first failure
cd ../..
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

- **Run in CI**: Let GitHub Actions handle full test runs
- **Debug Locally**: Run specific tests with `--headed` flag for visual debugging
- **Check Screenshots**: Review failure screenshots for debugging
- **Use Helper Script**: `run_e2e_tests.sh` handles environment setup automatically
- **Serial Execution**: Tests run one at a time by default (no parallel execution)
