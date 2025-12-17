"""Shared state definitions for the Pydantic AI demo agent.

This module keeps the graph state/data models small and serialisable so we can
use `pydantic_graph` persistence later without refactoring. Fields are chosen to
mirror the legacy `llm.StategraphAgent` dict keys while remaining optional
because nodes only fill the pieces they care about.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """
    State that flows through the agent graph.
    Each node can read and modify this state.
    """

    # ============================================================================
    # INPUT (Set at start)
    # ============================================================================

    user_query: str = ""
    """The original user research query"""

    project_id: str = ""
    """Project ID for storing/retrieving papers - REQUIRED for real mode"""

    # ============================================================================
    # EXTRACTED INFO (Set by early nodes)
    # ============================================================================

    keywords: list[str] = field(default_factory=list)
    """Keywords extracted from the query"""

    has_filter_instructions: bool = False
    """Whether the query contains filter instructions (dates, citations, etc.)"""

    # ============================================================================
    # QUALITY CONTROL (Set by QC node)
    # ============================================================================

    qc_decision: str = ""
    """Quality control decision: "accept", "reformulate", "split", "out_of_scope" """

    qc_explanation: str = ""
    """Explanation for the QC decision"""

    # ============================================================================
    # PAPERS (Set by retrieve/filter nodes)
    # ============================================================================

    papers_raw: list[dict[str, Any]] = field(default_factory=list)
    """Raw papers retrieved from database/APIs"""

    papers_filtered: list[dict[str, Any]] = field(default_factory=list)
    """Papers after applying filters"""

    # ============================================================================
    # RESULTS (Set by final nodes)
    # ============================================================================

    no_results_summary: str = ""
    """Explanation when no papers pass filters"""

    storage_result: str = ""
    """Result message from storing papers"""

    # ============================================================================
    # CONTROL FLAGS
    # ============================================================================

    requires_user_input: bool = False
    """Whether to pause and ask user for input"""

    is_out_of_scope: bool = False
    """Whether query is outside scientific literature scope"""


@dataclass
class AgentOutput:
    """Lightweight container returned when the graph ends."""

    status: str
    detail: dict[str, Any] = field(default_factory=dict)
