from __future__ import annotations

import re
from typing import Iterable, List, Tuple


class TitleVerificationError(Exception):
    """Raised when the agent output contains titles not present in the prompt."""


def _normalise(title: str) -> str:
    """
    Canonicalise a title for reliable comparison:
    - trim outer whitespace
    - collapse multiple spaces
    - lower‑case
    - strip trailing punctuation (. , ; :)
    """
    title = title.strip()
    title = re.sub(r"\s+", " ", title)          # collapse spaces/tabs/newlines
    title = title.rstrip(".,;:")                # remove trailing punctuation
    return title.lower()


def parse_prompt_titles(prompt: str) -> set[str]:
    """
    Split the prompt string into a set of canonicalised titles.
    Empty lines are ignored.
    """
    lines = [line for line in prompt.splitlines() if line.strip()]
    return {_normalise(line) for line in lines}


def verify_agent_titles(prompt: str, agent_titles: Iterable[str]) -> List[str]:
    """
    Verify that each agent‑returned title exists in the original prompt list.

    Returns the canonicalised list if all pass,
    else raises TitleVerificationError with diagnostics.
    """
    allowed = parse_prompt_titles(prompt)
    cleaned: List[Tuple[str, str]] = [
        (orig, _normalise(orig)) for orig in agent_titles
    ]

    illegal = [
        raw for raw, canon in cleaned if canon not in allowed
    ]
    if illegal:
        raise TitleVerificationError(
            f"Agent returned {len(illegal)} unknown title(s): {illegal!r}"
        )

    # Optional: warn/raise for duplicates
    canonical_values = [canon for _, canon in cleaned]
    if len(canonical_values) != len(set(canonical_values)):
        raise TitleVerificationError("Agent output contains duplicate titles.")

    # Success – return the *original* strings in the same order
    return [raw for raw, _ in cleaned]

if __name__ == "__main__":
    prompt_text = """
    Large‑Scale Pre‑training for Robotics
    Few‑Shot Learning with Transformers
    Efficient Vision Models for Edge Devices
    """.strip()

    cases = [
        (
            "### First case: All titles are present in the prompt",
            [
                "Few‑Shot Learning with Transformers",
                "Large‑Scale Pre‑training for Robotics",
            ],
        ),
        (
            "### Second case: All titles are present in the prompt, but one title is hallucinated",
            [
                "Few‑Shot Learning with Transformers",
                "Large‑Scale Pre‑training for Robotics",
                "The capstone project is the coolest project",  # hallucinated
            ],
        ),
        (
            "### Third case: All titles are present in the prompt, but one title is duplicated",
            [
                "Few‑Shot Learning with Transformers",
                "Few‑Shot Learning with Transformers",  # duplicate
                "Large‑Scale Pre‑training for Robotics",
            ],
        ),
    ]

    for banner, agent_titles in cases:
        print("\n" + banner)
        try:
            verified = verify_agent_titles(prompt_text, agent_titles)
            print("✅  Verification passed:", verified)
        except TitleVerificationError as exc:
            print("❌  Verification failed:", exc)