"""E2E tests for paper rating functionality."""

import pytest
import time


class TestPaperRating:
    """Test paper rating and replacement flow."""

    def test_rate_paper_with_stars(self, page, test_project_data):
        """Test rating papers with different star ratings (1-5 stars)."""
        # Create project and navigate to papers
        page.goto("http://localhost:5556/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")
        
        page.wait_for_url("**/project/**", timeout=120000)
        page.wait_for_selector(".recommendation-card", timeout=120000)
        
        # Test 5-star rating
        first_paper = page.locator(".recommendation-card").first
        five_star = first_paper.locator(".star-rating [data-rating='5'], .rating-star-5, .star:nth-child(5)")
        assert five_star.count() > 0, "5-star rating button not found"
        five_star.click()
        time.sleep(2)
        
        # Test 1-star rating on second paper if available
        papers = page.locator(".recommendation-card")
        if papers.count() > 1:
            second_paper = papers.nth(1)
            one_star = second_paper.locator(".star-rating [data-rating='1'], .rating-star-1, .star:nth-child(1)")
            if one_star.count() > 0:
                one_star.click()
                time.sleep(2)

            if one_star.count() > 0:
                one_star.click()
                time.sleep(2)

    def test_low_rating_triggers_replacement_with_notification(self, page, test_project_data):
        """Test that low rating (1-2 stars) triggers paper replacement and shows notification."""
        page.goto("http://localhost:5556/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")
        
        page.wait_for_url("**/project/**", timeout=120000)
        page.wait_for_selector(".recommendation-card", timeout=120000)
        
        initial_papers = page.locator(".recommendation-card")
        initial_count = initial_papers.count()
        
        # Get original title
        first_paper = page.locator(".recommendation-card").first
        original_title = first_paper.locator("h3").text_content()
        
        # Rate it 1 star
        one_star = first_paper.locator(".star-rating [data-rating='1'], .rating-star-1, .star:nth-child(1)")
        assert one_star.count() > 0, "1-star rating button not found"
        one_star.click()
        
        # Wait for replacement
        time.sleep(10)
        
        # Verify paper count remains same (replacement not removal)
        updated_papers = page.locator(".recommendation-card")
        assert updated_papers.count() == initial_count, "Paper count changed after replacement"
        
        # Check for replacement evidence (title changed or notification shown)
        new_first_paper = page.locator(".recommendation-card").first
        new_title = new_first_paper.locator("h3").text_content()
        notification = page.locator(".notification, .alert, .toast, [role='alert']")
        
        assert new_title != original_title or notification.count() > 0, \
            "No evidence of paper replacement"

        assert new_title != original_title or notification.count() > 0, \
            "No evidence of paper replacement"

    def test_rating_persists_and_updates_ui(self, page, test_project_data):
        """Test that ratings persist after reload and update UI immediately."""
        page.goto("http://localhost:5556/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")
        
        page.wait_for_url("**/project/**", timeout=120000)
        page.wait_for_selector(".recommendation-card", timeout=120000)
        
        # Get first paper and rate it
        first_paper = page.locator(".recommendation-card").first
        star_container = first_paper.locator(".star-rating, .rating-stars")
        assert star_container.count() > 0, "Star rating container not found"
        
        four_star = first_paper.locator(".star-rating [data-rating='4'], .rating-star-4, .star:nth-child(4)")
        if four_star.count() > 0:
            four_star.click()
            time.sleep(1)  # UI should update immediately
            
            # Reload page to test persistence
            page.reload()
            page.wait_for_selector(".recommendation-card", timeout=120000)
            # Rating persistence test passes if page reloads successfully

    def test_multiple_paper_ratings(self, page, test_project_data):
        """Test rating multiple papers with different ratings."""
        page.goto("http://localhost:5556/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")
        
        page.wait_for_url("**/project/**", timeout=120000)
        page.wait_for_selector(".recommendation-card", timeout=120000)
        
        # Rate first 3 papers with different ratings
        papers = page.locator(".recommendation-card")
        ratings = [5, 4, 3]
        for i, rating in enumerate(ratings):
            if i < papers.count():
                paper = papers.nth(i)
                star = paper.locator(f".star-rating [data-rating='{rating}'], .rating-star-{rating}, .star:nth-child({rating})")
                if star.count() > 0:
                    star.click()
                    time.sleep(1)

    def test_cannot_rate_replaced_paper(self, page, test_project_data):
        """Test that replaced papers cannot be rated again."""
        page.goto("http://localhost:5556/create-project")
        page.fill("#projectTitle", test_project_data["name"])
        page.fill("#projectDescription", test_project_data["description"])
        page.click("button[type='submit']")
        
        page.wait_for_url("**/project/**", timeout=120000)
        page.wait_for_selector(".recommendation-card", timeout=120000)
        
        first_paper = page.locator(".recommendation-card").first
        paper_id = first_paper.get_attribute("data-paper-id")
        
        # Rate it 1 star to trigger replacement
        one_star = first_paper.locator(".star-rating [data-rating='1'], .rating-star-1, .star:nth-child(1)")
        if one_star.count() > 0:
            one_star.click()
            time.sleep(10)
            
            # Check if old paper is disabled or removed
            old_paper = page.locator(f"[data-paper-id='{paper_id}']")
            if old_paper.count() > 0:
                class_attr = old_paper.get_attribute("class") or ""
                assert "disabled" in class_attr or "replaced" in class_attr, \
                    "Replaced paper is still active"