"""
Demo test that intentionally fails to showcase screenshot capture feature.

This test demonstrates how Playwright automatically captures screenshots
when tests fail, which is useful for debugging visual issues.
"""

import pytest
from tests.e2e.conftest import TestTimeouts


class TestScreenshotDemo:
    """Demo tests that intentionally fail to showcase screenshot capture."""

    def test_intentional_ui_mismatch(self, page, flask_server):
        """
        This test intentionally fails to demonstrate screenshot capture.

        It looks for an element that doesn't exist, causing the test to fail.
        The conftest.py fixture will automatically capture a screenshot on failure.
        """
        # Navigate to homepage
        page.goto(flask_server)

        # Wait for page to load
        page.wait_for_selector("h1", timeout=5000)

        # This assertion will FAIL intentionally - looking for non-existent element
        # This triggers screenshot capture in conftest.py
        assert page.locator("#this-element-does-not-exist").is_visible(), (
            "Intentionally failing - demonstrating screenshot capture feature"
        )

    def test_wrong_text_assertion(self, page, flask_server):
        """
        This test fails due to incorrect text assertion.

        Demonstrates screenshot capture when assertions don't match expected values.
        """
        # Navigate to create project page
        page.goto(f"{flask_server}/create-project")

        # Wait for page to load
        page.wait_for_selector("h1", timeout=5000)

        # Get the actual heading text
        heading = page.locator("h1").inner_text()

        # This will FAIL - expecting wrong text
        assert heading == "This Is The Wrong Title", (
            f"Expected 'This Is The Wrong Title' but got '{heading}' - screenshot will be captured"
        )

    def test_element_count_mismatch(self, page, test_project_data, flask_server):
        """
        This test fails due to incorrect element count.

        Creates a project and expects wrong number of papers to demonstrate
        screenshot capture during recommendation workflow.
        """
        # Create a project
        page.goto(f"{flask_server}/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        # Wait for redirect and papers to load
        page.wait_for_url("**/project/**", timeout=TestTimeouts.PROJECT_CREATION)
        page.wait_for_selector(".recommendation-card", timeout=TestTimeouts.PAPER_LOAD)

        # Count actual paper cards
        actual_count = page.locator(".recommendation-card").count()

        # This will FAIL - expecting impossible number
        expected_count = 999
        assert actual_count == expected_count, (
            f"Expected {expected_count} papers but found {actual_count} - screenshot captures current UI state"
        )

    @pytest.mark.skip(reason="Demo test - enable to see passing screenshot example")
    def test_passing_example_no_screenshot(self, page, flask_server):
        """
        This test passes, so NO screenshot is captured.

        Demonstrates that screenshots are only taken on failures.
        """
        page.goto(flask_server)
        assert page.locator("h1").is_visible()
        # No screenshot will be saved for this test
