"""E2E tests for paper recommendations flow."""

import pytest
import time


class TestRecommendationsFlow:
    """Test the full project creation and recommendations flow."""

    def test_create_project_and_get_recommendations(self, page, test_project_data):
        """Test creating a project and receiving recommendations."""
        # Navigate to create project page
        page.goto("/create-project")

        # Fill in project details
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])

        # Submit the form
        page.click("button[type='submit']")

        # Wait for redirect to project page (with generous timeout for SSE processing)
        page.wait_for_url("**/project/**", timeout=120000)

        # Verify we're on the project page
        assert "/project/" in page.url

        # Wait for project title to appear
        page.wait_for_selector("#projectTitleDisplay", timeout=10000)

        # Wait for papers to load via SSE (generous timeout)
        # The papers should start appearing within 60 seconds
        try:
            page.wait_for_selector(".recommendation-card", timeout=120000)
            # Verify at least one paper loaded
            papers = page.locator(".recommendation-card")
            assert papers.count() > 0, "No papers loaded"
        except Exception:
            # If papers don't appear, check for error messages
            error_text = page.text_content("body")
            pytest.fail(
                f"Papers failed to load within timeout period. Page text: {error_text[:500]}"
            )

    def test_paper_metadata_display(self, page, test_project_data):
        """Test that paper cards display all required metadata."""
        # Create project and navigate to papers
        page.goto("/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        # Wait for dashboard and click project
        page.wait_for_url("**/project/**", timeout=120000)

        # Wait for papers to load
        page.wait_for_selector(".recommendation-card", timeout=120000)

        # Get the first paper card using locator
        first_paper = page.locator(".recommendation-card").first
        assert first_paper.count() > 0, "No paper cards found"

        # Verify paper title exists (h3 element)
        title = first_paper.locator("h3")
        assert title.count() > 0, "Paper title not found"
        assert len(title.text_content().strip()) > 0, "Paper title is empty"

        # Verify authors (p element containing 👥 emoji) - optional as some papers may not have authors
        authors = first_paper.locator("p:has-text('👥')")
        if authors.count() > 0:
            authors_text = authors.text_content()
            assert "👥" in authors_text, "Authors emoji missing"
            assert "Authors:" in authors_text, "Authors label missing"

        # Verify year (p element containing 📅 emoji)
        year = first_paper.locator("p:has-text('📅')")
        assert year.count() > 0, "Year not found"
        year_text = year.text_content()
        assert "📅" in year_text, "Year emoji missing"
        assert "Year:" in year_text, "Year label missing"

        # Verify venue (p element containing 🏛️ emoji) - only check if venue exists
        # Note: Some papers may not have venue information
        venue = first_paper.locator("p:has-text('🏛️')")
        if venue.count() > 0:
            venue_text = venue.text_content()
            assert "🏛️" in venue_text, "Venue emoji missing"
            assert "Venue:" in venue_text, "Venue label missing"

        citations_text = first_paper.text_content()
        has_citations = "Citations" in citations_text
        has_fwci = "FWCI" in citations_text

        assert has_citations or has_fwci, (
            "At least one citation metric (Citations or FWCI) should be present"
        )

    def test_pdf_and_open_access_buttons(self, page, test_project_data):
        """Test PDF button and Open Access badge display."""
        # Create project and navigate to papers
        page.goto("/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        # Wait for dashboard and click project (CI needs more time)
        page.wait_for_url("**/project/**", timeout=120000)

        # Wait for papers to load (CI needs more time)
        page.wait_for_selector(".recommendation-card", timeout=120000)

        # Get the first paper card
        first_paper = page.locator(".recommendation-card").first

        # Check for PDF button (look for clickable element with "PDF" text)
        pdf_button = first_paper.locator("span:has-text('PDF')")
        if pdf_button.count() > 0:
            # Verify it has proper styling (blue background)
            button_html = pdf_button.evaluate("el => el.outerHTML")
            assert "007bff" in button_html.lower(), (
                "PDF button should have blue styling"
            )

        # Check for Open Access badge (look for element with 🔓 or 🔒)
        card_text = first_paper.text_content()
        if "🔓" in card_text or "Open Access" in card_text:
            # Found Open Access badge
            oa_badge = first_paper.locator("span:has-text('Open Access')")
            assert oa_badge.count() > 0, "Open Access badge not properly displayed"
        elif "🔒" in card_text or "Closed Access" in card_text:
            # Found Closed Access badge
            assert True  # Closed access is also valid

    def test_read_paper_link(self, page, test_project_data):
        """Test that Read Paper link is present and positioned correctly."""
        # Create project and navigate to papers
        page.goto("/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        # Wait for dashboard and click project
        page.wait_for_url("**/project/**", timeout=120000)

        # Wait for papers to load
        page.wait_for_selector(".recommendation-card", timeout=120000)

        # Get the first paper card
        first_paper = page.locator(".recommendation-card").first

        # Check for Read Paper link (button with "Read Paper" text)
        read_link = first_paper.locator("span:has-text('Read Paper')")
        assert read_link.count() > 0, "Read Paper link not found"

        # Verify it has onclick with window.open
        read_link_html = read_link.evaluate("el => el.outerHTML")
        assert "onclick" in read_link_html, "Read Paper link has no click handler"
        assert "window.open" in read_link_html, (
            "Read Paper link doesn't open new window"
        )

    def test_search_papers(self, page, test_project_data):
        """Test searching papers by keyword."""
        # Create project and navigate to papers
        page.goto("/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        # Wait for dashboard and click project
        page.wait_for_url("**/project/**", timeout=120000)

        # Wait for papers to load
        page.wait_for_selector(".recommendation-card", timeout=120000)

        # Get initial paper count
        initial_papers = page.locator(".recommendation-card")
        initial_count = initial_papers.count()

        # Search for a specific term (using title search input)
        search_input = page.locator("#titleSearchInput")
        if search_input.count() > 0:
            # Get the first paper's title to search for
            first_paper_title = page.locator(".recommendation-card").first.locator("h3")
            first_word = first_paper_title.text_content().split()[0]

            # Enter search term
            search_input.fill(first_word)

            # Wait a moment for filtering
            time.sleep(1)

            # Get filtered papers
            filtered_papers = page.locator(".recommendation-card")

            # At least the first paper should still be visible
            assert filtered_papers.count() > 0, "Search filtered out all papers"
            assert filtered_papers.count() <= initial_count, (
                "Search returned more papers than initial"
            )

    def test_filter_by_rating(self, page, test_project_data):
        """Test filtering papers by rating."""
        # Create project and navigate to papers
        page.goto("/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        # Wait for dashboard and click project
        page.wait_for_url("**/project/**", timeout=120000)

        # Wait for papers to load
        page.wait_for_selector(".recommendation-card", timeout=120000)

        # Look for rating filter dropdown/select
        rating_filter = page.locator("#rating-filter, select[name*='rating' i]")
        if rating_filter.count() > 0:
            # Get initial count
            initial_papers = page.locator(".recommendation-card")
            initial_count = initial_papers.count()

            # Select a rating filter
            rating_filter.select_option("5")

            # Wait for filtering
            time.sleep(1)

            # Get filtered papers
            filtered_papers = page.locator(".recommendation-card")

            # Filtered count should be <= initial count
            assert filtered_papers.count() <= initial_count

    def test_sse_connection_established(self, page, test_project_data):
        """Test that SSE connection is established for recommendations."""
        # Create project and navigate to papers
        page.goto("/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        # Wait for redirect to project page
        page.wait_for_url("**/project/**", timeout=120000)

        # Wait for papers to appear (confirms SSE worked)
        page.wait_for_selector(".recommendation-card", timeout=120000)

        # Verify multiple papers loaded
        papers = page.locator(".recommendation-card")
        assert papers.count() > 0, "No papers loaded via SSE"

    def test_paper_count_matches_request(self, page, test_project_data):
        """Test that the number of papers matches the requested count."""
        # Default paper count is 10
        requested_count = 10

        page.goto("/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        # Wait for dashboard and click project
        page.wait_for_url("**/project/**", timeout=120000)

        # Wait for papers to load (all of them)
        page.wait_for_selector(".recommendation-card", timeout=120000)

        # Wait a bit more to ensure all papers have loaded
        time.sleep(5)

        # Count papers
        papers = page.locator(".recommendation-card")
        actual_count = papers.count()

        # Should match or be close (within 1-2 due to possible failures)
        assert actual_count >= requested_count - 2, (
            f"Expected ~{requested_count} papers, got {actual_count}"
        )
        assert actual_count <= requested_count + 2, (
            f"Expected ~{requested_count} papers, got {actual_count}"
        )
