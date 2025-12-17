"""
Tooling for Pydantic AI state graph.
Integrates with existing llm/tools implementation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import os
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Toolbelt:
    """
    Complete toolbelt that wraps all existing tool implementations.
    Provides mock and real modes for testing and production.
    """

    use_mock: bool = field(default=True)
    seed_papers: list[dict[str, Any]] = field(default_factory=list)

    # ============================================================================
    # SCOPE DETECTION
    # ============================================================================

    def detect_out_of_scope(self, query: str) -> bool:
        """
        Detect if query is out of scope for scientific literature search.
        Real: Uses LLM-based scope detection from existing tools.
        Mock: Simple keyword matching.
        """
        if self.use_mock:
            return self._mock_detect_out_of_scope(query)

        from llm.tools.paper_handling_tools import detect_out_of_scope_query

        try:
            result_json = detect_out_of_scope_query(query)
            result = json.loads(result_json)

            is_out = result.get("status") == "out_of_scope"
            logger.info(f"Scope check: {result.get('status')} - {result.get('reason')}")
            return is_out

        except Exception as e:
            logger.error(f"Scope detection failed: {e}")
            return self._mock_detect_out_of_scope(query)

    def _mock_detect_out_of_scope(self, query: str) -> bool:
        """Mock scope detection."""
        lowered = query.lower()
        out_of_scope_terms = {"recipe", "joke", "weather", "movie", "restaurant"}
        return any(term in lowered for term in out_of_scope_terms)

    # ============================================================================
    # KEYWORD EXTRACTION
    # ============================================================================

    def extract_keywords(self, query: str) -> list[str]:
        """
        Extract keywords from query.
        Real: Uses LLM-based extraction from detect_out_of_scope_query.
        Mock: Simple word splitting.
        """
        if self.use_mock:
            return self._mock_extract_keywords(query)

        from llm.tools.paper_handling_tools import detect_out_of_scope_query

        try:
            result_json = detect_out_of_scope_query(query)
            result = json.loads(result_json)

            keywords = result.get("keywords", [])
            if keywords:
                logger.info(f"Extracted keywords: {keywords}")
                return keywords
            else:
                return self._mock_extract_keywords(query)

        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return self._mock_extract_keywords(query)

    def _mock_extract_keywords(self, query: str) -> list[str]:
        """Mock keyword extraction."""
        return [token.strip(",.?!") for token in query.split() if len(token) > 4]

    # ============================================================================
    # QUALITY CONTROL
    # ============================================================================

    def qc_decision(self, query: str, keywords: list[str]) -> tuple[str, str]:
        """
        Quality control decision.
        Returns: (decision, explanation)
        Decisions: "accept", "reformulate", "split", "out_of_scope"
        """
        if self.use_mock:
            return self._mock_qc_decision(query, keywords)

        query_lower = query.lower()

        # Check for empty/short queries
        if not query.strip() or len(query.strip()) < 10:
            return "out_of_scope", "Query is too short or empty"

        # Check keywords
        if len(keywords) < 2:
            return "reformulate", "Query needs more specific search terms"

        # Check for comparison queries that should be split
        if any(
            ind in query_lower
            for ind in ["compare", "versus", "vs", "difference between"]
        ):
            if query_lower.count(" and ") >= 2 or query_lower.count(",") >= 2:
                return (
                    "split",
                    "Multiple comparisons detected - splitting will give better results",
                )

        # Check for multiple questions
        if query.count("?") > 1:
            return "split", "Multiple questions detected - splitting recommended"

        # Check if too broad
        if len(keywords) > 15:
            return (
                "reformulate",
                "Query is too broad - please focus on specific aspects",
            )

        return "accept", "Query is clear and specific"

    def _mock_qc_decision(self, query: str, keywords: list[str]) -> tuple[str, str]:
        """Mock QC."""
        if not query.strip():
            return "out_of_scope", "Empty questions cannot be answered"
        if len(keywords) < 2:
            return "reformulate", "Need more than one keyword for context"
        if "compare" in query.lower():
            return "split", "Comparison requests usually need sub-queries"
        return "accept", "Looks good"

    # ============================================================================
    # FILTER DETECTION
    # ============================================================================

    def detect_filters(self, query: str) -> bool:
        """Detect if query contains filtering instructions."""
        if self.use_mock:
            return any(token in query.lower() for token in {"after", "before", "since"})

        filter_indicators = {
            "after",
            "before",
            "since",
            "until",
            "between",
            "from",
            "recent",
            "latest",
            "last year",
            "past",
            "this year",
            "highly cited",
            "more than",
            "at least",
            "citations",
            "published in",
            "only",
            "exclude",
            "without",
            "except",
        }
        return any(indicator in query.lower() for indicator in filter_indicators)

    # ============================================================================
    # PAPER RETRIEVAL - KEY METHOD
    # ============================================================================

    def retrieve_papers(
        self, keywords: list[str], project_id: str, count: int = 20
    ) -> list[dict[str, Any]]:
        """
        Retrieve papers using existing tools.

        Real mode:
          1. Updates paper database with new papers (update_papers_for_project)
          2. Gets best matching papers (get_best_papers)

        Mock mode: Returns dummy papers

        Args:
            keywords: Search keywords extracted from query
            project_id: Project ID for storing/retrieving papers
            count: Number of papers to retrieve

        Returns:
            List of paper dictionaries
        """

        if self.use_mock:
            return self._mock_retrieve_papers(keywords, count)

        # Import real tools here

        from llm.tools.paper_handling_tools import update_papers_for_project
        from llm.tools.paper_ranker import get_best_papers as rank_best_papers

        try:
            # Step 1: Update database with new papers
            logger.info(
                f"Updating papers for project {project_id} with keywords: {keywords}"
            )
            update_result = update_papers_for_project(keywords, project_id)
            logger.info(f"Update result: {update_result}")

            # Step 2: Get best papers using ranking
            logger.info(f"Retrieving {count} best papers")
            papers = rank_best_papers(project_id, count)

            if papers:
                logger.info(f"Retrieved {len(papers)} papers")
                return papers
            else:
                logger.warning("No papers retrieved, falling back to mock")
                return self._mock_retrieve_papers(keywords, count)

        except Exception as e:
            logger.error(f"Paper retrieval failed: {e}")
            # Fallback to mock on error
            return self._mock_retrieve_papers(keywords, count)

    def _mock_retrieve_papers(
        self, keywords: list[str], count: int
    ) -> list[dict[str, Any]]:
        """Mock paper retrieval."""
        if self.seed_papers:
            return self.seed_papers[:count]

        # Generate dummy papers based on keywords
        query_str = " ".join(keywords[:3])
        return [
            {
                "paper_id": f"mock-{i}",
                "paper_hash": f"demo-{i}",
                "title": f"Research on {query_str} - Paper {i}",
                "abstract": f"This paper explores {query_str}. We present novel findings and methodologies.",
                "authors": ["Smith, J.", "Doe, A."],
                "year": 2024 - (i % 3),
                "citations": 10 * (count - i),
                "cited_by_count": 10 * (count - i),
                "doi": f"10.1234/mock.{i}",
            }
            for i in range(1, count + 1)
        ]

    # ============================================================================
    # PAPER FILTERING
    # ============================================================================

    async def filter_papers(
        self,
        query: str,
        raw: list[dict[str, Any]],
        has_filters: bool,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Filter papers based on natural language criteria.
        Real: Uses LLM-based filter_papers_by_nl_criteria.
        Mock: Simple title matching.
        """
        if self.use_mock:
            return self._mock_filter_papers(query, raw, has_filters)

        if not has_filters:
            return raw, {
                "explanation": "No filters to apply",
                "applied_filters": [],
                "total_evaluated": len(raw),
                "passed_filter": len(raw),
            }

        try:
            # Use existing LLM-based filtering
            from llm.tools.paper_handling_tools import filter_papers_by_nl_criteria

            result_json = filter_papers_by_nl_criteria(raw, query)
            result = json.loads(result_json)

            if result.get("status") == "success":
                filtered = result.get("kept_papers", [])
                criteria = {
                    "explanation": result.get("reasoning", "Applied filters"),
                    "applied_filters": list(result.get("filters", {}).keys()),
                    "total_evaluated": len(raw),
                    "passed_filter": result.get("kept_count", len(filtered)),
                }
                logger.info(f"Filtered {len(raw)} → {len(filtered)} papers")
                return filtered, criteria
            else:
                logger.warning(f"Filtering failed: {result.get('message')}")
                return raw, {
                    "explanation": f"Filter error: {result.get('message')}",
                    "applied_filters": ["error"],
                    "total_evaluated": len(raw),
                    "passed_filter": len(raw),
                }

        except Exception as e:
            logger.error(f"Filter papers failed: {e}")
            return self._mock_filter_papers(query, raw, has_filters)

    def _mock_filter_papers(
        self, query: str, raw: list[dict[str, Any]], has_filters: bool
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Mock filtering."""
        if not has_filters:
            return raw, {"explanation": "No filters"}

        # Simple keyword matching
        query_words = set(query.lower().split())
        filtered = [
            paper
            for paper in raw
            if any(word in paper.get("title", "").lower() for word in query_words)
        ]

        # Keep at least a few papers
        if len(filtered) < 3:
            filtered = raw[: min(5, len(raw))]

        return filtered, {
            "explanation": "Mock filter kept papers with matching titles",
            "applied_filters": ["mock_title_match"],
            "total_evaluated": len(raw),
            "passed_filter": len(filtered),
        }

    # ============================================================================
    # PAPER STORAGE
    # ============================================================================

    def store(self, project_id: str | None, papers: list[dict[str, Any]]) -> str:
        """
        Store papers to database.
        Real: Uses store_papers_for_project.
        Mock: Returns success message.
        """
        if self.use_mock:
            return self._mock_store(project_id, papers)

        if not project_id:
            return "Skipped storage: no project id provided"

        from llm.tools.paper_handling_tools import store_papers_for_project

        try:
            # Papers should have: paper_hash, summary
            result = store_papers_for_project(project_id, papers)
            logger.info(f"Storage result: {result}")
            return result

        except Exception as e:
            logger.error(f"Storage failed: {e}")
            return f"Storage failed: {str(e)}"

    def _mock_store(self, project_id: str | None, papers: list[dict[str, Any]]) -> str:
        """Mock storage."""
        if not project_id:
            return "Skipped storage: no project id"
        return f"[MOCK] Stored {len(papers)} papers for project {project_id}"

    # ============================================================================
    # ADDITIONAL TOOLS (Optional - can be called directly from nodes if needed)
    # ============================================================================

    def reformulate_query_tool(
        self, keywords: list[str], query_description: str
    ) -> dict:
        """Wrapper for reformulate_query tool."""
        if self.use_mock:
            return {
                "status": "success",
                "result": {
                    "reformulated_description": query_description,
                    "refined_keywords": keywords,
                },
            }

        try:
            from llm.tools.paper_handling_tools import reformulate_query

            result_json = reformulate_query(keywords, query_description)
            return json.loads(result_json)
        except Exception as e:
            logger.error(f"Query reformulation failed: {e}")
            return {"status": "error", "message": str(e)}

    def narrow_query_tool(self, query_description: str, keywords: list[str]) -> dict:
        """Wrapper for narrow_query tool."""
        if self.use_mock:
            return {"status": "success", "narrowed_keywords": keywords[:5]}

        try:
            from llm.tools.paper_handling_tools import narrow_query

            result_json = narrow_query(query_description, keywords)
            return json.loads(result_json)
        except Exception as e:
            logger.error(f"Query narrowing failed: {e}")
            return {"status": "error", "message": str(e)}

    def broaden_query_tool(
        self, keywords: list[str], query_description: str = ""
    ) -> dict:
        """Wrapper for retry_broaden tool."""
        if self.use_mock:
            return {
                "status": "success",
                "broadened_keywords": keywords + ["additional"],
            }

        try:
            from llm.tools.paper_handling_tools import retry_broaden

            result_json = retry_broaden(keywords, query_description)
            return json.loads(result_json)
        except Exception as e:
            logger.error(f"Query broadening failed: {e}")
            return {"status": "error", "message": str(e)}


@dataclass(slots=True)
class AgentDeps:
    """Dependencies injected into every node via `GraphRunContext.deps`."""

    tools: Toolbelt = field(default_factory=lambda: Toolbelt(use_mock=True))


def create_agent_deps(use_mock: bool | None = None) -> AgentDeps:
    """
    Factory function to create agent dependencies.

    Args:
        use_mock: Whether to use mock tools. If None, reads from environment.
    """
    if use_mock is None:
        use_mock = os.getenv("USE_MOCK_TOOLS", "true").lower() == "true"

    return AgentDeps(tools=Toolbelt(use_mock=use_mock))
