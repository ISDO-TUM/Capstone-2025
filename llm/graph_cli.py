"""CLI helper for exporting the Pydantic graph as Mermaid text."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Literal

if __package__ in (None, ""):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from llm.agent import Input, build_agent_graph


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
    code = graph.mermaid_code(start_node=Input, direction=direction)
    if save_path is not None:
        path = Path(save_path)
        path.write_text(code, encoding="utf-8")
    return code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "graph cli")
    parser.add_argument(
        "--direction",
        default="LR",
        choices=("TB", "BT", "LR", "RL"),
        help="Mermaid diagram direction (default: LR)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional file path to save the diagram text",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    diagram = generate_mermaid_diagram(direction=args.direction, save_path=args.output)
    print(diagram)
    if args.output:
        print(f"\nSaved diagram to {args.output.resolve()}")


if __name__ == "__main__":
    main()
