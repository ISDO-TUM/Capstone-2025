"""
Pytest configuration and fixtures for E2E tests.

This module provides:
- Flask server fixture for testing
- Browser page fixtures from Playwright
- Test data fixtures
- Database cleanup utilities
"""

import pytest
import threading
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
    Enable TEST_MODE and mock LLM for deterministic E2E tests.

    This replaces the real LLM with a mock to ensure:
    - Consistent test results (no API variability)
    - No API costs
    - Faster test execution
    - No rate limits

    Also sets all database connection parameters for PostgreSQL.
    """

    # Mock the LLM to avoid API calls and ensure deterministic responses
    import llm.LLMDefinition as llm_def
    from tests.e2e.mock_llm import MockedLLM
    import llm.Embeddings as embeddings_module
    from unittest.mock import MagicMock

    # Store original LLM
    original_llm = llm_def.LLM

    # Replace with mock
    llm_def.LLM = MockedLLM

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

    # Restore original LLM and client after tests
    llm_def.LLM = original_llm
    embeddings_module.client = original_client

    # Cleanup environment variables
    os.environ.pop("TEST_MODE", None)


@pytest.fixture(scope="session")
def flask_server(enable_test_mode):
    """
    Start Flask app in a background thread for testing.

    Args:
        enable_test_mode: Ensures environment variables are set before importing app

    Yields:
        str: Base URL of the test server (e.g., 'http://127.0.0.1:5556')
    """
    from app import app
    import socket

    # Use a dynamic port if preferred port is taken
    preferred_port = 5556
    test_port = preferred_port

    def find_free_port(start_port, max_attempts=10):
        """Find an available port starting from start_port."""
        for port in range(start_port, start_port + max_attempts):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except OSError:
                    continue
        raise RuntimeError(
            f"Could not find free port in range {start_port}-{start_port + max_attempts}"
        )

    test_port = find_free_port(preferred_port)

    # Flag to track server status
    server_started = threading.Event()
    server_error = []

    def run_app():
        try:
            app.config["TESTING"] = True
            # Signal that we're about to start
            server_started.set()
            app.run(host="127.0.0.1", port=test_port, debug=False, use_reloader=False)
        except Exception as e:
            server_error.append(e)
            server_started.set()

    thread = threading.Thread(target=run_app, daemon=True)
    thread.start()

    # Wait for server to start
    server_started.wait(timeout=5)
    if server_error:
        raise RuntimeError(f"Failed to start server: {server_error[0]}")

    # Give Flask a moment to fully initialize
    time.sleep(2)

    # Verify server is responding
    max_retries = 10
    for i in range(max_retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", test_port)) == 0:
                    break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        raise RuntimeError(f"Server did not start successfully on port {test_port}")

    base_url = f"http://127.0.0.1:{test_port}"

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

        # Enable console logging for debugging
        page_instance.on("console", lambda msg: print(f"Browser console: {msg.text}"))

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

        # Create project
        page.goto("/create-project")
        page.fill("#projectTitle", "Shared Test Project")
        page.fill(
            "#projectDescription",
            "machine learning artificial intelligence neural networks deep learning computer vision",
        )
        page.click("button[type='submit']")

        # Wait for redirect to project page
        page.wait_for_url("**/project/**", timeout=60000)
        project_url = page.url

        # Wait for papers to load
        page.wait_for_selector(".recommendation-card", timeout=60000)

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
