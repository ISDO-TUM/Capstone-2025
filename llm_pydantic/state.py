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
    """Mutable state that flows through the graph run."""

    user_query: str = ""
    project_id: str | None = None
    keywords: list[str] = field(default_factory=list)
    qc_decision: str = "pending"
    qc_reason: str = ""
    has_filter_instructions: bool = False
    out_of_scope_message: str | None = None
    papers_raw: list[dict[str, Any]] = field(default_factory=list)
    papers_filtered: list[dict[str, Any]] = field(default_factory=list)
    requires_user_input: bool = False
    no_results_summary: str | None = None
    final_payload: dict[str, Any] | None = None


@dataclass
class AgentOutput:
    """Lightweight container returned when the graph ends."""

    status: str
    detail: dict[str, Any] = field(default_factory=dict)
