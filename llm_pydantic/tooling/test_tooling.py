"""
Pytest-only integration tests for Pydantic AI tooling.
"""

from __future__ import annotations

import os
import pytest

from llm_pydantic.tooling.tooling import create_agent_deps
from llm.state import AgentState

# ---------------------------------------------------------------------------
# Pytest configuration
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(params=["mock"])  # later: ["mock", "real"]
def use_mock(request) -> bool:
    """
    Controls whether tooling runs in mock or real mode.

    Start with mock only.
    Add "real" when infra is ready.
    """
    use_mock = request.param == "mock"
    os.environ["USE_MOCK_TOOLS"] = "true" if use_mock else "false"
    return use_mock


@pytest.fixture
def deps(use_mock: bool):
    """Agent dependencies."""
    return create_agent_deps(use_mock=use_mock)


# ---------------------------------------------------------------------------
# Individual tool tests
# ---------------------------------------------------------------------------


async def test_scope_detection(deps):
    tools = deps.tools

    assert tools.detect_out_of_scope("recipe for chocolate cake") is True
    assert tools.detect_out_of_scope("machine learning in healthcare") is False


async def test_keyword_extraction(deps):
    tools = deps.tools

    query = "recent advances in CRISPR gene editing for cancer treatment"
    keywords = tools.extract_keywords(query)

    assert isinstance(keywords, list)
    assert len(keywords) >= 2
    assert all(isinstance(k, str) for k in keywords)


async def test_quality_control(deps):
    tools = deps.tools

    decision, reason = tools.qc_decision(
        "machine learning in drug discovery",
        ["machine", "learning", "drug", "discovery"],
    )

    assert decision in {"accept", "reformulate", "split", "out_of_scope"}
    assert isinstance(reason, str)


async def test_filter_detection(deps):
    tools = deps.tools

    assert tools.detect_filters("papers published after 2020") is True
    assert tools.detect_filters("machine learning research") is False


# ---------------------------------------------------------------------------
# End-to-end tooling workflow (node-equivalent)
# ---------------------------------------------------------------------------


async def test_complete_tooling_workflow(deps):
    tools = deps.tools

    state = AgentState(
        user_query=(
            "machine learning applications in drug discovery published after 2020"
        ),
        project_id="pytest-project",
    )

    # ---------------------------------------------------------------------
    # Scope check (ScopeCheckNode equivalent)
    # ---------------------------------------------------------------------
    is_out = tools.detect_out_of_scope(state.user_query)
    assert is_out is False

    # ---------------------------------------------------------------------
    # Keyword extraction (InputNode)
    # ---------------------------------------------------------------------
    state.keywords = tools.extract_keywords(state.user_query)
    assert len(state.keywords) >= 2

    # ---------------------------------------------------------------------
    # Quality control (QualityControlNode)
    # ---------------------------------------------------------------------
    decision, reason = tools.qc_decision(state.user_query, state.keywords)
    assert decision == "accept"

    # ---------------------------------------------------------------------
    # Filter detection
    # ---------------------------------------------------------------------
    state.has_filter_instructions = tools.detect_filters(state.user_query)
    assert state.has_filter_instructions is True

    # ---------------------------------------------------------------------
    # Retrieval (RetrievePapersNode)
    # ---------------------------------------------------------------------
    state.papers_raw = tools.retrieve_papers(
        keywords=state.keywords,
        project_id=state.project_id,
        count=10,
    )

    assert isinstance(state.papers_raw, list)
    assert len(state.papers_raw) > 0

    # ---------------------------------------------------------------------
    # Filtering (FilterPapersNode)
    # ---------------------------------------------------------------------
    state.papers_filtered, criteria = await tools.filter_papers(
        query=state.user_query,
        raw=state.papers_raw,
        has_filters=state.has_filter_instructions,
    )

    assert isinstance(criteria, dict)
    assert "explanation" in criteria
    assert len(state.papers_filtered) > 0

    # ---------------------------------------------------------------------
    # Storage (StorePapersNode)
    # ---------------------------------------------------------------------
    papers_to_store = [
        {
            "paper_hash": p.get("paper_hash", p.get("paper_id", f"hash-{i}")),
            "summary": "Relevant to the query",
        }
        for i, p in enumerate(state.papers_filtered)
    ]

    result = tools.store(
        project_id=state.project_id,
        papers=papers_to_store,
    )

    assert isinstance(result, str)
    assert "Stored" in result or "MOCK" in result or "Skipped" in result
