"""E2E tests for project deletion functionality."""

import time


class TestDeleteProject:
    """Test the delete project functionality."""

    def test_delete_project_button_exists(self, page, test_project_data):
        """Test that delete button appears on project cards in React dashboard."""
        # Create a project first
        page.goto("/create-project")
        page.wait_for_load_state("networkidle")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        # Wait for redirect to project page
        page.wait_for_url("**/project/**", timeout=10000)

        # Go back to dashboard
        page.goto("/")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Wait for project cards to load (React component)
        page.wait_for_selector(".project-card", timeout=10000)

        # Check that delete button exists
        delete_btn = page.locator(".delete-project-btn").first
        assert delete_btn.count() > 0, "Delete button not found on project card"
        assert delete_btn.is_visible(), "Delete button is not visible"

    def test_delete_project_flow(self, page, test_project_data):
        """Test the complete delete project flow in React app."""
        # Create a project
        page.goto("/create-project")
        page.wait_for_load_state("networkidle")
        page.fill("#projectTitle", "Project to Delete")
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        # Wait for redirect
        page.wait_for_url("**/project/**", timeout=10000)

        # Go to dashboard
        page.goto("/")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Wait for project card to appear
        page.wait_for_selector(".project-card", timeout=10000)

        # Get initial count of projects
        initial_count = page.locator(".project-card").count()
        assert initial_count > 0, "No projects found"

        # Find and click the delete button
        delete_btn = page.locator(".delete-project-btn").first

        # Set up dialog handler to accept confirmation
        page.on("dialog", lambda dialog: dialog.accept())

        # Click delete button
        delete_btn.click()

        # Wait for the project card to be removed
        time.sleep(2)

        # Verify project count decreased
        new_count = page.locator(".project-card").count()
        assert new_count == initial_count - 1, (
            f"Project count should decrease by 1: {initial_count} -> {new_count}"
        )

    def test_delete_project_confirmation_cancel(self, page, test_project_data):
        """Test that canceling delete confirmation doesn't delete the project in React app."""
        # Create a project
        page.goto("/create-project")
        page.wait_for_load_state("networkidle")
        page.fill("#projectTitle", "Project Not to Delete")
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        # Wait for redirect
        page.wait_for_url("**/project/**", timeout=10000)

        # Go to dashboard
        page.goto("/")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Wait for project card
        page.wait_for_selector(".project-card", timeout=10000)

        # Get initial count
        initial_count = page.locator(".project-card").count()

        # Set up dialog handler to DISMISS confirmation
        page.on("dialog", lambda dialog: dialog.dismiss())

        # Click delete button
        delete_btn = page.locator(".delete-project-btn").first
        delete_btn.click()

        # Wait a moment
        time.sleep(1)

        # Verify project count unchanged
        current_count = page.locator(".project-card").count()
        assert current_count == initial_count, (
            "Project should not be deleted when confirmation is canceled"
        )

    def test_delete_multiple_projects(self, page, test_project_data):
        """Test deleting multiple projects one after another."""
        # Create first project
        page.goto("/create-project")
        page.fill("#projectTitle", "First Project")
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")
        page.wait_for_url("**/project/**", timeout=10000)

        # Create second project
        page.goto("/create-project")
        page.fill("#projectTitle", "Second Project")
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")
        page.wait_for_url("**/project/**", timeout=10000)

        # Go to dashboard
        page.goto("/")
        time.sleep(2)

        # Wait for projects to load
        page.wait_for_selector(".project-card", timeout=10000)

        # Get initial count (should have at least 2)
        initial_count = page.locator(".project-card").count()
        assert initial_count >= 2, "Should have at least 2 projects"

        # Set up dialog handler to accept all confirmations
        page.on("dialog", lambda dialog: dialog.accept())

        # Delete first project
        page.locator(".delete-project-btn").first.click()
        time.sleep(2)

        # Verify count decreased by 1
        count_after_first = page.locator(".project-card").count()
        assert count_after_first == initial_count - 1, (
            f"First deletion failed: {initial_count} -> {count_after_first}"
        )

        # Delete second project
        page.locator(".delete-project-btn").first.click()
        time.sleep(2)

        # Verify count decreased by 1 again
        count_after_second = page.locator(".project-card").count()
        assert count_after_second == count_after_first - 1, (
            f"Second deletion failed: {count_after_first} -> {count_after_second}"
        )

    def test_delete_button_styling(self, page, test_project_data):
        """Test that delete button has proper styling and hover effects."""
        # Create a project
        page.goto("/create-project")
        page.fill("#projectTitle", "Style Test Project")
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")
        page.wait_for_url("**/project/**", timeout=10000)

        # Go to dashboard
        page.goto("/")
        time.sleep(2)

        # Wait for project card
        page.wait_for_selector(".project-card", timeout=10000)

        # Get delete button
        delete_btn = page.locator(".delete-project-btn").first

        # Check button exists (may not be visible until hover)
        assert delete_btn.count() > 0, "Delete button should exist"

        # Check button has SVG icon
        svg_icon = delete_btn.locator("svg")
        assert svg_icon.count() > 0, "Delete button should have SVG icon"

        # Hover over card to make button visible
        project_card = page.locator(".project-card").first
        project_card.hover()
        time.sleep(0.5)

        # Button should be visible after hovering on card
        assert delete_btn.is_visible(), "Delete button should be visible on card hover"
