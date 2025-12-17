"""CLI helper for exporting the Pydantic graph as Mermaid text."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from llm_pydantic.agent import generate_mermaid_diagram


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
