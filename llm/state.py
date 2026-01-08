from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentState:
    """
    State that flows through the agent graph.
    Each node can read and modify this state.
    """

    all_papers: list[dict[str, Any]] = field(default_factory=list)
    applied_filter_criteria: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    has_filter_instructions: Optional[bool] = None
    keywords: list[str] = field(default_factory=list)
    no_results_message: Any = None
    out_of_scope_message: Any = None
    out_of_scope_result: str = ""
    papers_filtered: Any = None
    papers_raw: Any = None
    project_id: str = ""
    qc_decision: str = ""
    qc_decision_reason: str = ""
    qc_tool_result: Optional[str] = None
    requires_user_input: bool = False
    store_papers_for_project_result: Any = None
    subqueries: Any = None
    update_papers_by_project_result: Any = None
    user_query: str = ""


@dataclass
class AgentOutput:
    """Lightweight container returned when the graph ends."""

    status: str = "no status"
