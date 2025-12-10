"""Minimal CLI entrypoint for driving the Pydantic graph agent."""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

from pydantic_graph import End

# Ensure project root is on sys.path when running this module directly
if __package__ in (None, ""):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from llm_pydantic.agent import build_agent_graph
from llm_pydantic.nodes.input_node import InputNode
from llm_pydantic.state import AgentState
from llm_pydantic.tooling import AgentDeps

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _safe_parse_json(payload: str):
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload


def _print_payload(payload) -> None:
    if isinstance(payload, str):
        payload = _safe_parse_json(payload)
    if isinstance(payload, (dict, list)):
        print(json.dumps(payload, indent=2))
    else:
        print(payload)


def _abbreviate_title(text: str, max_length: int = 80) -> str:
    """Return a concise title snippet for CLI logging."""
    if not text:
        return "Untitled paper"
    text = text.strip()
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


async def _run_agent_stream_async(user_query: str):
    graph = build_agent_graph()
    state = AgentState()
    deps = AgentDeps()
    step = 0
    print("Streaming agent thoughts (pydantic graph)")
    async with graph.iter(InputNode(user_message=user_query), state=state, deps=deps) as run:
        async for node in run:
            step += 1
            if isinstance(node, End):
                print(f"\nStep {step}: Agent finished.")
                
                if run.result is None:
                    print("No result returned by agent.")
                    return None
                result = run.result.output
                if result:
                    print("Payload:")
                    _print_payload(result.detail)
                return result
            thought = getattr(node, "thought", None)
            if not thought:
                thought = f"Running {node.__class__.__name__}"
            print(f"\nStep {step}: {thought}")
    return None


def run_agent_stream(user_query: str):
    return asyncio.run(_run_agent_stream_async(user_query))


def main() -> None:
    user_query = "Machine learning for healthcare after 2018"

    project_name = f"CLI Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    project_id = project_name.replace(" ", "-")

    logger.info("Using synthetic project '%s'", project_name)

    final_query = f"{user_query} project ID: {project_id}"
    print("Using project:", project_id)
    print("User query:", final_query)
    result = run_agent_stream(final_query)

    if not result:
        print("\nAgent did not return a payload.")
        return

    payload = result.detail or {}
    papers = payload.get("items", [])

    print(f"\nRetrieved {len(papers)} papers for project {project_id}")
    for idx, paper in enumerate(papers, start=1):
        title = paper.get("title", "No title available")
        short_title = _abbreviate_title(title)
        paper_hash = paper.get("paper_hash", "N/A")
        print(f"{idx:2d}. {short_title} (hash {paper_hash[:8]}...)")


if __name__ == "__main__":
    main()
