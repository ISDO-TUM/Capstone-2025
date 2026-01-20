"""
LLM agent configuration for the Capstone project.

Responsibilities:
- Loads OpenAI API key
- Defines the default PydanticAI agent
- Exposes a single entry-point agent for text generation
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent
from pydantic import BaseModel
from pydantic_ai.models.openai import OpenAIModel

from config import OPENAI_API_KEY

# Check if we're in TEST_MODE
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"

if not TEST_MODE and not OPENAI_API_KEY:
    raise ValueError(
        "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    )


class TextResponse(BaseModel):
    text: str


@dataclass
class LLMResponse:
    content: str
    raw: Any | None = None


TextAgent = Agent(
    model=OpenAIModel(
        model_name="gpt-5.1",
        api_key=OPENAI_API_KEY,
    ),
    result_type=TextResponse,
)


async def run_llm(prompt: str) -> LLMResponse:
    """
    Minimal compatibility layer.
    This is the function nodes should call for now.
    """
    result = await TextAgent.run(prompt)
    return LLMResponse(
        content=result.data.text,
        raw=result,
    )


# Mock LLM for TEST_MODE
class MockLLM:
    """Mock LLM that returns deterministic responses for testing."""

    def __init__(self, **kwargs):
        self.model = kwargs.get("model", "mock-gpt")
        self.temperature = kwargs.get("temperature", 0)

    def invoke(self, prompt: Any) -> LLMResponse:
        """Return mock responses based on prompt content."""
        prompt_text = str(prompt).lower()

        # Newsletter recommendation prompt - extract actual paper hashes
        if "select the top" in prompt_text and "paper" in prompt_text:
            # Extract paper hashes from the prompt (they're hex strings)
            import re

            # Look for "paper_hash" or similar patterns followed by hex strings
            hash_pattern = r"['\"]paper_hash['\"]:\s*['\"]([a-f0-9]{64})['\"]"
            hashes = re.findall(hash_pattern, str(prompt))

            if hashes:
                # Return first 2 hashes found (or all if less than 2)
                k = min(2, len(hashes))
                content = json.dumps(
                    [
                        {
                            "paper_hash": hashes[i],
                            "summary": f"Mock summary {i + 1}: This paper is relevant to your research interests.",
                        }
                        for i in range(k)
                    ]
                )
            else:
                # Fallback if no hashes found
                content = json.dumps([])
        # Out of scope detection
        elif "out of scope" in prompt_text or "out-of-scope" in prompt_text:
            content = json.dumps(
                {
                    "status": "valid",
                    "keywords": ["machine learning", "healthcare", "papers"],
                }
            )
        # Filter detection
        elif "filter" in prompt_text and "detection" in prompt_text:
            content = json.dumps(
                {
                    "has_filter_instructions": False,
                    "reason": "No specific filters detected",
                }
            )
        # QC decision
        elif "qc_decision" in prompt_text or "quality control" in prompt_text:
            content = json.dumps(
                {"qc_decision": "accept", "reason": "Query is clear and specific"}
            )
        # Default response
        else:
            content = json.dumps({"status": "success", "message": "Mock LLM response"})

        return LLMResponse(content=content, raw=None)

    def __call__(self, prompt: Any) -> LLMResponse:
        return self.invoke(prompt)


if TEST_MODE:
    # Use mock LLM in test mode
    _models = {
        "gpt-5.1": MockLLM(model="mock-gpt-5.1", temperature=0.3),
        "gpt-5": MockLLM(model="mock-gpt-5", temperature=0.3),
        "gpt-5-mini": MockLLM(model="mock-gpt-5-mini", temperature=0.3),
        "gpt-5-nano": MockLLM(model="mock-gpt-5-nano", temperature=0.3),
    }
    LLM = _models["gpt-5.1"]
else:
    # Use the real LLM
    LLM = run_llm
