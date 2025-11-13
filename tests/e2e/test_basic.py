"""
Basic E2E test to verify the testing setup works.

This test creates a project and verifies the page loads correctly.
"""

import pytest
from playwright.sync_api import Page, expect


def test_homepage_loads(page: Page):
    """Test that the homepage loads successfully"""
    page.goto("/")
    
    # Verify dashboard header is visible
    expect(page.locator("h1")).to_be_visible()
    
    # Verify create project button exists
    expect(page.locator("#createProjectBtn, button:has-text('Create')")).to_be_visible()


def test_create_project_page_loads(page: Page):
    """Test that the create project page loads"""
    page.goto("/create-project")
    
    # Verify form elements exist
    expect(page.locator("#projectTitle")).to_be_visible()
    expect(page.locator("#projectDescription")).to_be_visible()
    expect(page.locator("button[type='submit']")).to_be_visible()


def test_create_project_basic(page: Page, test_project_data):
    """Test creating a basic project and verifying it loads"""
    # Navigate to create project page
    page.goto("/create-project")
    
    # Fill in project details
    page.fill("#projectTitle", test_project_data["name"])
    page.fill("#projectDescription", test_project_data["description"])
    
    # Submit form
    page.click("button[type='submit']")
    
    # Wait for redirect to project overview page (not dashboard)
    page.wait_for_url("**/project/**", timeout=10000)
    
    # Verify we're on the project page
    assert "/project/" in page.url
    
    # Wait for project title to be populated (loaded via JS/API)
    page.wait_for_selector("#projectTitleDisplay", timeout=10000)
    expect(page.locator("#projectTitleDisplay")).to_have_text(test_project_data["name"], timeout=10000)
