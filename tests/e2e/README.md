# E2E Testing Guide

This directory contains end-to-end tests for the Capstone-2025 application using Playwright and Pytest.

## Quick Start

### Running Tests Locally

**⚠️ IMPORTANT: E2E tests require TEST_MODE=true**

Tests use a special test mode that:
- Bypasses Clerk authentication (uses mock user)
- Builds frontend with test-specific configuration
- Enables deterministic test behavior

#### Prerequisites
- **Docker & Docker Compose** installed
- **uv** and virtual environment set up
- **Playwright** installed (`playwright install chromium`)

#### Step 1: Start Services with TEST_MODE

**Mac/Linux:**
```bash
# From project root
cd /path/to/Capstone-2025

# Build and start ALL services with TEST_MODE enabled
TEST_MODE=true docker compose up -d --build

# Verify services are running
docker compose ps
```

**Windows (PowerShell):**
```powershell
# From project root
cd C:\path\to\Capstone-2025

# Build and start ALL services with TEST_MODE enabled
$env:TEST_MODE="true"
docker compose up -d --build

# Verify services are running
docker compose ps
```

**What TEST_MODE does:**
- **Backend**: Bypasses Clerk authentication, uses mock test user
- **Frontend**: Builds with test configuration, skips ClerkProvider
- **nginx**: Uses local proxy configuration for backend API

#### Step 2: Run Tests

```bash
# Run all E2E tests
uv run pytest tests/e2e/ -v

# Run specific test file
uv run pytest tests/e2e/test_basic.py -v

# Run specific test
uv run pytest tests/e2e/test_basic.py::test_homepage_loads -v
```

#### Step 3: Stop Services

```bash
# When done testing
docker compose down
```

### Running for Local Development (Without Tests)

If you want to run the app normally (with real Clerk authentication):

```bash
# Start without TEST_MODE (default is false)
docker compose up -d

# App runs at http://localhost with real authentication
```

**Note:** E2E tests will **NOT work** without TEST_MODE=true.

## Test Coverage

The E2E test suite covers:

### 1. Basic Functionality (`test_basic.py`)
- Homepage loads correctly
- Create project page loads
- Basic project creation flow

### 2. Delete Project (`test_delete_project.py`)
- Delete button exists on project cards
- Complete delete project flow with confirmation
- Cancel deletion (confirmation modal)
- Delete multiple projects
- Delete button styling validation

### 3. Recommendations Flow (`test_recommendations.py`)
- Complete project creation → recommendations workflow
- Paper metadata display (authors, year, venue, citations, FWCI, percentile)
- PDF button and Open Access badge rendering
- "Read Paper" link positioning
- Search and filter functionality
- SSE connection establishment
- Paper count validation

### 4. Paper Rating (`test_paper_rating.py`)
- Rating papers with 1-5 stars
- Low rating (1-2 stars) triggers replacement
- Rating persistence after page reload
- Multiple paper ratings
- Notification on replacement
- UI updates on rating
- Cannot rate replaced papers

### 5. Load More Papers (`test_load_more.py`)
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
│   ├── test_delete_project.py   # Project deletion tests
│   ├── test_recommendations.py  # Full recommendation flow
│   ├── test_paper_rating.py     # Rating and replacement tests
│   └── test_load_more.py        # Load More functionality
└── README.md                    # This file
```

## Running Specific Tests

**Prerequisites:** Services must be running with `TEST_MODE=true docker compose up -d --build`

### Run All E2E Tests
```bash
uv run pytest tests/e2e/ -v
```

### Run Specific Test File
```bash
uv run pytest tests/e2e/test_basic.py -v
```

### Run Specific Test Class
```bash
uv run pytest tests/e2e/test_recommendations.py::TestRecommendationsFlow -v
```

### Run Single Test
```bash
uv run pytest tests/e2e/test_basic.py::test_homepage_loads -v
```

### Run with Verbose Output
```bash
uv run pytest tests/e2e/ -vv
```

## Debugging

**Prerequisites:** Services running with `TEST_MODE=true docker compose up -d --build`

### View Browser During Tests
```bash
uv run pytest tests/e2e/ --headed
```

### Slow Down Execution
```bash
uv run pytest tests/e2e/ --headed --slowmo=1000
```

### Run Single Test with Debugging
```bash
uv run pytest tests/e2e/test_load_more.py::TestLoadMorePapers::test_load_more_button_exists_and_increases_count -v
```

### View Screenshots
Failed tests automatically save screenshots to `tests/e2e/screenshots/`.

### Pytest Debugging Options
```bash
uv run pytest tests/e2e/ -v -s          # Show print statements
uv run pytest tests/e2e/ -v --pdb       # Drop into debugger on failure
uv run pytest tests/e2e/ -v --maxfail=1 # Stop after first failure
```

### Check Docker Services
```bash
# Verify all services are running
docker compose ps

# Check backend logs
docker compose logs web

# Check frontend logs
docker compose logs frontend

# Restart services if needed
TEST_MODE=true docker compose restart
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
Verifies Docker Compose services are ready:
- Frontend (nginx) on http://localhost:80
- Backend (Flask API) on http://localhost:8080
- PostgreSQL on localhost:5432
- ChromaDB on localhost:8000

**Returns:** Base URL for testing (http://localhost)

### `page` (function scope)
Provides fresh Playwright Page for each test with:
- Viewport: 1920x1080
- Base URL: http://localhost
- Console and error logging enabled
- Screenshot capture on failure
- Test mode script injection

### `test_project_data`
Sample project data with name and description for testing.

### `enable_test_mode` (session scope, autouse)
Automatically enables TEST_MODE and Mock LLM:
- Replaces real LLM with Mock LLM (zero API calls, deterministic responses)
- Sets environment variables for testing
- Mocks OpenAI embeddings client

## Troubleshooting

### Tests Failing with Authentication Errors
```
Clerk authentication required
# OR
No papers loaded / Project creation fails
```
**Solution:**
```bash
# You MUST start services with TEST_MODE=true
docker compose down
TEST_MODE=true docker compose up -d --build

# Then run tests
uv run pytest tests/e2e/ -v
```

### Services Not Running
```
❌ Frontend (nginx) is not running on port 80
# OR
❌ Backend (Flask) is not running on port 8080
```
**Solution:**
```bash
# Check services status
docker compose ps

# Restart services with TEST_MODE
TEST_MODE=true docker compose up -d --build

# Check logs if services crash
docker compose logs web
docker compose logs frontend
```

### Port Already in Use
```
Bind for 0.0.0.0:80 failed: port is already allocated
```
**Solution:**
```bash
# Stop any existing containers
docker compose down

# Check what's using the port
lsof -i :80  # Mac/Linux
netstat -ano | findstr :80  # Windows

# Start fresh
TEST_MODE=true docker compose up -d --build
```

### Database Connection Error
```
psycopg2.OperationalError: connection failed
```
**Solution:**
```bash
# Reset database and restart
docker compose down -v
TEST_MODE=true docker compose up -d --build
```

### Playwright Not Found
```
ModuleNotFoundError: No module named 'playwright'
```
**Solution:**
```bash
uv sync
playwright install chromium
```

### Frontend Shows Real Clerk Login
**Problem:** Frontend wasn't built with TEST_MODE

**Solution:**
```bash
# Must rebuild with TEST_MODE to bake in test configuration
docker compose down
TEST_MODE=true docker compose up -d --build
```

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

- **Always Use TEST_MODE**: E2E tests require `TEST_MODE=true docker compose up -d --build`
- **Rebuild When Switching**: Frontend config is baked at build time - rebuild when switching between test/dev mode
- **Check Services First**: Run `docker compose ps` to verify all services are running before tests
- **Reset When Needed**: Use `docker compose down -v` to clear all data and start fresh
- **Debug with Logs**: Check `docker compose logs web` and `docker compose logs frontend` for errors
- **Run Specific Tests**: Don't run the full suite while debugging - target specific failing tests
- **Use --headed**: Add `--headed` flag to see browser during debugging
- **Check Screenshots**: Review failure screenshots in `tests/e2e/screenshots/`
- **Serial Execution**: Tests run one at a time to avoid database conflicts
