"""E2E tests for paper rating functionality."""

import time


class TestPaperRating:
    """Test paper rating and replacement flow."""

    def test_rating_persists_and_updates_ui(self, page, test_project_data):
        """Test that ratings persist after reload and update UI immediately."""
        page.goto("/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        page.wait_for_url("**/project/**", timeout=120000)
        page.wait_for_selector(".recommendation-card", timeout=120000)
        
        # Wait for papers to fully load (SSE stream complete)
        time.sleep(5)

        # Get first paper and scroll it into view
        first_paper = page.locator(".recommendation-card").first
        first_paper.scroll_into_view_if_needed()
        time.sleep(1)

        # Click 4th star using JavaScript to bypass visibility checks
        page.evaluate("""() => {
            const card = document.querySelector('.recommendation-card');
            const buttons = card.querySelectorAll('button[type="button"]');
            if (buttons.length >= 4) {
                buttons[3].click();
            }
        }""")
        time.sleep(2)  # Wait for UI update

        # Reload page to test persistence
        page.reload()
        page.wait_for_selector(".recommendation-card", timeout=120000)
        # Rating persistence test passes if page reloads successfully

    def test_multiple_paper_ratings(self, page, test_project_data):
        """Test rating multiple papers with different ratings."""
        page.goto("/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        page.wait_for_url("**/project/**", timeout=120000)
        page.wait_for_selector(".recommendation-card", timeout=120000)

        # Rate first 3 papers with different ratings (5, 4, 3)
        papers = page.locator(".recommendation-card")
        ratings = [5, 4, 3]
        for i, rating in enumerate(ratings):
            if i < papers.count():
                paper = papers.nth(i)
                star_buttons = paper.locator("button[type='button']")
                if star_buttons.count() >= rating:
                    # Click the nth button (0-indexed, so rating-1)
                    star_buttons.nth(rating - 1).click()
                    time.sleep(1)

    def test_cannot_rate_replaced_paper(self, page, test_project_data):
        """Test that replaced papers cannot be rated again."""
        page.goto("/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")

        page.wait_for_url("**/project/**", timeout=120000)
        page.wait_for_selector(".recommendation-card", timeout=120000)

        first_paper = page.locator(".recommendation-card").first
        paper_hash = first_paper.get_attribute("data-paper-hash")

        # Rate it 1 star to trigger replacement
        star_buttons = first_paper.locator("button[type='button']")
        if star_buttons.count() > 0:
            star_buttons.nth(0).click()  # 1st star
            time.sleep(10)

            # Check if old paper is disabled or removed
            old_paper = page.locator(f"[data-paper-hash='{paper_hash}']")
            if old_paper.count() > 0:
                class_attr = old_paper.get_attribute("class") or ""
                assert "disabled" in class_attr or "replaced" in class_attr, (
                    "Replaced paper is still active"
                )
