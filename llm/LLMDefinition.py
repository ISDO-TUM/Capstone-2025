"""
LLM model configuration and instantiation for the Capstone project.

Responsibilities:
- Loads OpenAI API key from environment
- Instantiates multiple ChatOpenAI models (GPT-4.1, GPT-4, etc.)
- Exposes the default LLM instance for use throughout the codebase
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from config import OPENAI_API_KEY

# Check if we're in TEST_MODE
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"

if not TEST_MODE and not OPENAI_API_KEY:
    raise ValueError(
        "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    )

_client = OpenAI(api_key=OPENAI_API_KEY)


@dataclass
class LLMResponse:
    content: str
    raw: Any | None = None


class OpenAIChatModel:
    """Lightweight wrapper exposing LangChain-like invoke semantics."""

    def __init__(self, client: OpenAI, model: str, temperature: float = 0.3) -> None:
        self._client = client
        self.model = model
        self.temperature = temperature

    def invoke(self, prompt: Any) -> LLMResponse:
        prompt_text = self._normalize_prompt(prompt)
        response = self._client.responses.create(
            model=self.model,
            input=prompt_text,
            temperature=self.temperature,
        )
        content = self._extract_text(response)
        return LLMResponse(content=content, raw=response)

    def __call__(self, prompt: Any) -> LLMResponse:
        return self.invoke(prompt)

    @staticmethod
    def _normalize_prompt(prompt: Any) -> str:
        if prompt is None:
            return ""
        if isinstance(prompt, str):
            return prompt
        if isinstance(prompt, (list, tuple)):
            return "\n".join(str(part) for part in prompt)
        if isinstance(prompt, dict):
            return json.dumps(prompt)
        return str(prompt)

    @staticmethod
    def _extract_text(response: Any) -> str:
        text_chunks: list[str] = []
        output = getattr(response, "output", None)
        if output:
            for item in output:
                item_type = getattr(item, "type", None)
                if item_type == "message":
                    contents = getattr(item, "content", []) or []
                    for content in contents:
                        if getattr(content, "type", None) == "output_text":
                            text_chunks.append(getattr(content, "text", ""))
                        elif hasattr(content, "text"):
                            text_chunks.append(str(content.text))
                elif item_type == "output_text":
                    text_chunks.append(getattr(item, "text", ""))
        if not text_chunks:
            for candidate in (
                getattr(response, "output_text", None),
                getattr(response, "content", None),
            ):
                if candidate:
                    if isinstance(candidate, list):
                        text_chunks.append("".join(str(part) for part in candidate))
                    else:
                        text_chunks.append(str(candidate))
                    break
        return "".join(text_chunks).strip()


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
                content = json.dumps([
                    {
                        "paper_hash": hashes[i],
                        "summary": f"Mock summary {i+1}: This paper is relevant to your research interests."
                    }
                    for i in range(k)
                ])
            else:
                # Fallback if no hashes found
                content = json.dumps([])
        # Out of scope detection
        elif "out of scope" in prompt_text or "out-of-scope" in prompt_text:
            content = json.dumps({
                "status": "valid",
                "keywords": ["machine learning", "healthcare", "papers"]
            })
        # Filter detection
        elif "filter" in prompt_text and "detection" in prompt_text:
            content = json.dumps({
                "has_filter_instructions": False,
                "reason": "No specific filters detected"
            })
        # QC decision
        elif "qc_decision" in prompt_text or "quality control" in prompt_text:
            content = json.dumps({
                "qc_decision": "accept",
                "reason": "Query is clear and specific"
            })
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
else:
    # Use real OpenAI models in production
    _client = OpenAI(api_key=OPENAI_API_KEY)
    _models = {
        "gpt-5.1": OpenAIChatModel(_client, model="gpt-5.1", temperature=0.3),
        "gpt-5": OpenAIChatModel(_client, model="gpt-5", temperature=0.3),
        "gpt-5-mini": OpenAIChatModel(_client, model="gpt-5-mini", temperature=0.3),
        "gpt-5-nano": OpenAIChatModel(_client, model="gpt-5-nano", temperature=0.3),
    }

LLM = _models["gpt-5.1"]


def get_llm(model_name: str):
    """
    Returns an LLM instance by model name.
    Args:
        model_name (str): The name of the model to return.
    Returns:
        ChatOpenAI: The LLM instance.
    """
    return _models.get(model_name)


def set_default_llm(model_name: str):
    """
    Sets the default LLM instance.
    Args:
        model_name (str): The name of the model to set as default.
    """
    global LLM
    llm_instance = get_llm(model_name)
    if llm_instance:
        LLM = llm_instance
    else:
        raise ValueError(f"Model '{model_name}' not found.")


def get_available_models():
    """
    Returns a list of available model names.
    """
    return list(_models.keys())
