"""Graph-powered agent entrypoint built with `pydantic_graph`.

The implementation mirrors the structure described in `llm/StategraphAgent.py`
but is intentionally lightweight: every tool call is backed by the
`MockToolbelt` so we can focus on wiring the graph described in the
`https://ai.pydantic.dev/graph/` docs.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable, Literal

from pydantic_graph import Graph

from llm_pydantic.nodes.filter_papers_node import FilterPapersNode
from llm_pydantic.nodes.input_node import InputNode
from llm_pydantic.nodes.no_results_node import NoResultsNode
from llm_pydantic.nodes.out_of_scope_node import OutOfScopeNode
from llm_pydantic.nodes.quality_control_node import QualityControlNode
from llm_pydantic.nodes.retrieve_papers_node import RetrievePapersNode
from llm_pydantic.nodes.scope_node import ScopeCheckNode
from llm_pydantic.nodes.store_papers_node import StorePapersNode
from llm_pydantic.state import AgentOutput, AgentState
from llm_pydantic.tooling import AgentDeps


def _node_registry() -> Iterable[type]:
	return (
		InputNode,
		ScopeCheckNode,
		QualityControlNode,
		RetrievePapersNode,
		FilterPapersNode,
		StorePapersNode,
		NoResultsNode,
		OutOfScopeNode,
	)


def build_agent_graph() -> Graph[AgentState, AgentDeps, AgentOutput]:
	"""Create the reusable graph instance for callers/tests."""

	return Graph(nodes=tuple(_node_registry()), state_type=AgentState)


async def run_agent(
	user_message: str,
	*,
	state: AgentState | None = None,
	deps: AgentDeps | None = None,
) -> AgentOutput:
	"""Helper that runs the graph for a single query."""

	graph = build_agent_graph()
	run_state = state or AgentState()
	run_deps = deps or AgentDeps()
	result = await graph.run(
		InputNode(user_message=user_message),
		state=run_state,
		deps=run_deps,
	)
	return result.output


def run_agent_sync(
	user_message: str,
	*,
	state: AgentState | None = None,
	deps: AgentDeps | None = None,
) -> AgentOutput:
	"""Synchronous convenience wrapper for quick experiments."""

	return asyncio.run(run_agent(user_message, state=state, deps=deps))


def generate_mermaid_diagram(
	*,
	direction: Literal["TB", "BT", "LR", "RL"] = "LR",
	save_path: str | Path | None = None,
) -> str:
	"""Return the Mermaid `stateDiagram-v2` definition for this graph.

	Optionally writes the diagram text to ``save_path`` so it can be visualised at
	https://mermaid.live/ or committed with docs.
	"""

	graph = build_agent_graph()
	code = graph.mermaid_code(start_node=InputNode, direction=direction)
	if save_path is not None:
		path = Path(save_path)
		path.write_text(code, encoding="utf-8")
	return code
