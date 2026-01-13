"""
Basic E2E test to verify the testing setup works.

This test creates a project and verifies the page loads correctly.
"""

from playwright.sync_api import Page, expect


def test_homepage_loads(page: Page):
    """Test that the React homepage loads successfully"""
    page.goto("/")
    page.wait_for_load_state("networkidle")

    # Wait for React app to render - check for main content
    expect(page.locator(".main-content")).to_be_visible(timeout=10000)


def test_create_project_page_loads(page: Page):
    """Test that the create project page loads in React app"""
    page.goto("/create-project")
    page.wait_for_load_state("networkidle")

    # Verify form elements exist in React CreateProject component
    expect(page.locator("#projectTitle")).to_be_visible(timeout=10000)
    expect(page.locator("#projectDescription")).to_be_visible(timeout=10000)
    expect(page.locator("button[type='submit']")).to_be_visible()


def test_create_project_basic(page: Page, test_project_data):
    """Test creating a basic project via React frontend"""
    # Navigate to create project page
    page.goto("/create-project")
    page.wait_for_load_state("networkidle")

    # Fill in project details using React form
    page.fill("#projectTitle", test_project_data["name"])
    page.fill("#projectDescription", test_project_data["description"])

    # Submit form
    page.click("button[type='submit']")

    # Wait for React Router to navigate to project overview
    page.wait_for_url("**/project/**", timeout=10000)

    # Verify we're on the project page
    assert "/project/" in page.url

    # Wait for project content to load
    expect(page.locator(".main-content")).to_be_visible(timeout=10000)
