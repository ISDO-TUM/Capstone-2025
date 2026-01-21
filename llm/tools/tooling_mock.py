"""Minimal mock tooling used by the Pydantic AI state graph demo.

The real `llm.StategraphAgent` pulls dozens of bespoke tools. For this first
pass we keep the surface area intentionally tiny so the graph wiring can be
reviewed without needing the upstream infra.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockToolbelt:
    """Very small facade that pretends to be our tool suite."""

    seed_papers: list[dict[str, Any]] = field(default_factory=list)

    def detect_out_of_scope(self, query: str) -> bool:
        lowered = query.lower()
        return any(term in lowered for term in {"recipe", "joke", "weather"})

    def extract_keywords(self, query: str) -> list[str]:
        return [token.strip(",.?!") for token in query.split() if len(token) > 4]

    def qc_decision(self, query: str, keywords: list[str]) -> tuple[str, str]:
        if not query.strip():
            return "out_of_scope", "Empty questions cannot be answered"
        if len(keywords) < 2:
            return "reformulate", "Need more than one keyword for context"
        if "compare" in query.lower():
            return "split", "Comparison requests usually need sub-queries"
        return "accept", "Looks good"

    def detect_filters(self, query: str) -> bool:
        return any(token in query.lower() for token in {"after", "before", "since"})

    def retrieve_papers(
        self,
        query: str | None = None,
        keywords: list[str] | None = None,
        project_id: str | None = None,
        count: int = 5,
    ) -> list[dict[str, Any]]:
        base = self.seed_papers or [
            {
                "paper_hash": f"demo-{i}",
                "title": f"Paper {i}",
                "abstract": "...",
            }
            for i in range(1, 8)
        ]
        return base[:count]

    def filter_papers(
        self,
        query: str,
        raw: list[dict[str, Any]],
        has_filters: bool,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if not has_filters:
            return raw, {}
        filtered = [paper for paper in raw if "Paper" in paper.get("title", "")]
        return filtered[:3], {"explanation": "Mock filter kept top 3 titles"}

    def store(self, project_id: str | None, papers: list[dict[str, Any]]) -> str:
        if not project_id:
            return "Skipped storage: no project id"
        return f"Stored {len(papers)} papers for project {project_id}"


@dataclass(slots=True)
class AgentDeps:
    """Dependencies injected into every node via `GraphRunContext.deps`."""

    tools: MockToolbelt = field(default_factory=MockToolbelt)
