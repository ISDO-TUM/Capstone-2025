"""
LLM agent configuration for the Capstone project.

Responsibilities:
- Loads OpenAI API key
- Defines the default PydanticAI agent
- Exposes a single entry-point agent for text generation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent
from pydantic import BaseModel
from pydantic_ai.models.openai import OpenAIModel

from config import OPENAI_API_KEY

if not OPENAI_API_KEY:
    raise ValueError(
        "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    )


class TextResponse(BaseModel):
    text: str


@dataclass
class LLMResponse:
    content: str
    raw: Any | None = (
        None
    )


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


LLM = run_llm
