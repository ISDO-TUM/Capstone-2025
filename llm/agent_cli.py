"""Minimal CLI entrypoint for driving the Stategraph agent stream."""

import json
import logging
import os
import sys
from datetime import datetime, timezone

# Ensure project root is on sys.path when running this module directly
if __package__ in (None, ""):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from database.papers_database_handler import get_paper_by_hash
from database.projectpaper_database_handler import get_papers_for_project
from database.projects_database_handler import add_new_project_to_db
from llm.agent import trigger_stategraph_agent_show_thoughts

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


def run_agent_stream(user_query: str, project_id: str, user_id: str) -> None:
    """Stream Stategraph agent updates to stdout for the given user query."""

    print("Streaming agent thoughts (matches web UI)")
    for idx, update in enumerate(
        trigger_stategraph_agent_show_thoughts(user_query, project_id, user_id), start=1
    ):
        thought = update.get("thought", "(no thought provided)")
        print(f"\nStep {idx}: {thought}")
        final_content = update.get("final_content")
        if final_content:
            print("Payload:")
            _print_payload(final_content)
        if update.get("is_final"):
            print("\nWorkflow complete.")
            break


def main() -> None:
    """
    Run a minimal CLI demo of the Stategraph agent backed by the project database.
    This script needs the postgres database to be running, but no web app and no ChromaDB.
    """

    user_id = "cli_test_user"
    user_query = "I am looking for papers in the field of machine learning in healthcare published after 2518."

    # Create a new project for this CLI session
    project_name = (
        f"CLI Session {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
    )
    project_description = "Temporary project created via agent_cli session"
    logger.info("Creating project '%s' for user %s", project_name, user_id)
    project_id = add_new_project_to_db(user_id, project_name, project_description, True)

    # Assemble final query
    final_query = f"{user_query} project ID: {project_id}"
    print("Using project:", project_id)
    print("User query:", final_query)
    run_agent_stream(final_query, project_id, user_id)

    project_papers = get_papers_for_project(project_id)

    print(f"\nRetrieved {len(project_papers)} papers for project {project_id}")
    for idx, entry in enumerate(project_papers, start=1):
        paper = get_paper_by_hash(entry.get("paper_hash"))
        if paper:
            title = paper.get("title", "No title available")
            short_title = _abbreviate_title(title)
        else:
            short_title = "Paper not found in db"

        paper_hash = entry.get("paper_hash", "N/A")
        print(f"{idx:2d}. {short_title} (hash {paper_hash[:8]}...)")


if __name__ == "__main__":
    main()
