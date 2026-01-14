"""
Pytest configuration and fixtures for E2E tests.

This module provides:
- Flask server fixture for testing
- Browser page fixtures from Playwright
- Test data fixtures
- Database cleanup utilities
"""

import pytest
import time
import os
import sys

# Set TEST_MODE before any other imports to prevent OpenAI API key check
os.environ["TEST_MODE"] = "true"
os.environ["OPENAI_API_KEY"] = "dummy-test-key"

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Centralized timeout configuration for E2E tests


class TestTimeouts:
    """Centralized timeout configuration for E2E tests."""

    PROJECT_CREATION = 120000  # 120 seconds for LLM processing (CI is slower)
    PAPER_LOAD = 120000  # 120 seconds for paper loading (CI is slower)
    SSE_STREAM = 120000  # For SSE event streams
    LOAD_MORE = 120000  # For load more button
    REPLACEMENT = 20000  # For paper replacement
    DEFAULT = 15000  # Default wait timeout


@pytest.fixture(scope="session", autouse=True)
def enable_test_mode():
    """
    Enable TEST_MODE and mock embeddings for deterministic E2E tests.

    Note: LLM mocking is now handled automatically by LLMDefinition.py
    when TEST_MODE=true is set. This fixture only needs to mock embeddings.

    This ensures:
    - Consistent test results (no API variability)
    - No API costs
    - Faster test execution
    - No rate limits
    """

    import llm.Embeddings as embeddings_module
    from unittest.mock import MagicMock

    # Mock the OpenAI client for embeddings
    mock_client = MagicMock()
    mock_embedding_response = MagicMock()
    mock_embedding_response.data = [
        MagicMock(embedding=[0.1] * 1536)
    ]  # Standard embedding size
    mock_client.embeddings.create.return_value = mock_embedding_response

    original_client = embeddings_module.client
    embeddings_module.client = mock_client

    yield

    # Restore original client after tests
    embeddings_module.client = original_client

    # Cleanup environment variables
    os.environ.pop("TEST_MODE", None)


@pytest.fixture(scope="session")
def flask_server(enable_test_mode):
    """
    Use Docker Compose services for E2E testing.

    This fixture assumes Docker Compose is running with:
    - React frontend (nginx) on http://localhost:80
    - Flask backend API on http://localhost:8080
    - PostgreSQL on localhost:5432
    - ChromaDB on localhost:8000

    Run tests with: docker compose up -d && pytest tests/e2e/ && docker compose down

    Args:
        enable_test_mode: Ensures environment variables are set before importing app

    Yields:
        str: Base URL of the React frontend (http://localhost)
    """
    import socket
    import requests

    base_url = "http://localhost"
    backend_url = "http://localhost:8080"

    # Verify services are running
    max_retries = 30
    services = {
        "Frontend (nginx)": ("localhost", 80),
        "Backend (Flask)": ("localhost", 8080),
        "PostgreSQL": ("localhost", 5432),
        "ChromaDB": ("localhost", 8000),
    }

    print("\nWaiting for Docker Compose services to be ready...")

    for service_name, (host, port) in services.items():
        print(f"Checking {service_name} on port {port}...")
        for i in range(max_retries):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex((host, port))
                    if result == 0:
                        print(f"✓ {service_name} is ready")
                        break
            except Exception:
                pass

            if i == max_retries - 1:
                raise RuntimeError(
                    f" {service_name} is not running on port {port}.\n"
                    f"Please start Docker Compose with: docker compose up -d"
                )
            time.sleep(1)

    # Verify backend API is responding
    try:
        response = requests.get(f"{backend_url}/api/clerk-config", timeout=5)
        if response.status_code == 200:
            print("Backend API is responding")
        else:
            print(f"⚠ Backend API returned status {response.status_code}")
    except Exception as e:
        raise RuntimeError(
            f"Backend API is not responding at {backend_url}\n"
            f"Error: {e}\n"
            f"Please ensure Docker Compose is running: docker compose up -d"
        )

    print(f"\n✓ All services ready. Testing against {base_url}\n")

    yield base_url


@pytest.fixture(scope="function")
def page(flask_server, request):
    """
    Provide a fresh browser page for each test.

    Args:
        flask_server: Base URL from flask_server fixture
        request: Pytest request object for test info

    Yields:
        Page: Playwright Page object with base_url set
    """
    from playwright.sync_api import sync_playwright
    from pathlib import Path

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # Set to False for debugging
            slow_mo=0,  # Add delay between actions (ms) for debugging
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            base_url=flask_server,
            locale="en-US",
            ignore_https_errors=True,
        )

        page_instance = context.new_page()

        # Inject script to set test mode BEFORE the app JavaScript loads
        page_instance.add_init_script("""
            // Set test mode flag for React app
            window.__CLERK_TEST_MODE__ = true;
            
            // Override fetch to add Authorization header to API calls
            const originalFetch = window.fetch;
            window.fetch = function(url, options = {}) {
                if (typeof url === 'string' && url.includes('/api/') && !url.includes('/api/clerk-config')) {
                    options.headers = options.headers || {};
                    if (typeof options.headers.set === 'function') {
                        options.headers.set('Authorization', 'Bearer mock-jwt-token');
                    } else {
                        options.headers['Authorization'] = 'Bearer mock-jwt-token';
                    }
                }
                return originalFetch(url, options);
            };
        """)

        # Filter console logs to suppress expected errors
        def handle_console(msg):
            # Suppress common expected errors during tests
            suppressed_patterns = [
                "Failed to load resource: the server responded with a status of 400",
                "Failed to rate paper",
            ]
            if not any(pattern in msg.text for pattern in suppressed_patterns):
                print(f"Browser console: {msg.text}")

        page_instance.on("console", handle_console)

        # Enable error logging
        page_instance.on("pageerror", lambda err: print(f"Browser error: {err}"))

        yield page_instance

        # Capture screenshot on test failure
        if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
            # Create screenshots directory if it doesn't exist
            # Use __file__ to get the directory of this conftest.py
            screenshots_dir = Path(__file__).parent / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            # Generate screenshot filename from test name
            test_name = request.node.name
            screenshot_path = screenshots_dir / f"{test_name}_failure.png"

            # Capture screenshot
            page_instance.screenshot(path=str(screenshot_path))
            print(f"\n Screenshot saved: {screenshot_path}")

        context.close()
        browser.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to access test results for screenshot capture.

    This allows the page fixture to check if a test failed.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture
def test_project_data():
    """
    Sample project data for testing.

    Returns:
        dict: Project name and description
    """
    return {
        "name": "Test Project E2E",
        "description": "deep learning models for computer vision and image recognition using convolutional neural networks",
    }


@pytest.fixture
def out_of_scope_data():
    """
    Out-of-scope query data for testing agent detection.

    Returns:
        dict: Project with non-academic query
    """
    return {
        "title": "Out of Scope Test",
        "description": "How are you today? What's the weather like? Tell me a joke.",
    }


@pytest.fixture(scope="module")
def shared_project(flask_server):
    """
    Create a single project shared across multiple tests in a module.

    This dramatically speeds up test execution by avoiding redundant
    project creation (which takes 60+ seconds per project).

    Returns:
        dict: Project URL and data
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(base_url=flask_server)
        page = context.new_page()

        # Navigate to React create project page
        page.goto("/create-project")
        page.wait_for_load_state("networkidle")

        # Fill React form
        page.fill("#projectTitle", "Shared Test Project")
        page.fill(
            "#projectDescription",
            "machine learning artificial intelligence neural networks deep learning computer vision",
        )
        page.click("button[type='submit']")

        # Wait for React Router redirect to project page
        page.wait_for_url("**/project/**", timeout=60000)
        project_url = page.url

        # Wait for papers to load via SSE
        page.wait_for_selector(".recommendation-card", timeout=120000)

        context.close()
        browser.close()

        return {
            "url": project_url,
            "name": "Shared Test Project",
            "description": "machine learning artificial intelligence neural networks deep learning computer vision",
        }


@pytest.fixture
def wait_for_papers_loaded(page):
    """Helper fixture to wait for papers to finish loading."""

    def _wait():
        # Wait for at least one paper card
        page.wait_for_selector(".recommendation-card", timeout=60000)
        # Wait for loading indicators to disappear (if any)
        page.wait_for_function(
            """() => {
                const loadingIndicators = document.querySelectorAll('.loading, .spinner, [data-loading="true"]');
                return loadingIndicators.length === 0;
            }""",
            timeout=5000,
        ).catch(lambda: None)  # Ignore if no loading indicators

    return _wait


# Optional: Database cleanup fixture
# Uncomment and modify if you want to clean test data after each test
# @pytest.fixture(autouse=True)
# def cleanup_test_data():
#     """Clean up test data after each test"""
#     yield
#     # Add cleanup logic here
#     # e.g., delete test projects from database
