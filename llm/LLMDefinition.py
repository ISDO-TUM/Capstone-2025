"""
LLM model configuration and instantiation for the Capstone project.

Responsibilities:
- Loads OpenAI API key from environment
- Instantiates multiple ChatOpenAI models (GPT-4.1, GPT-4, etc.)
- Exposes the default LLM instance for use throughout the codebase
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from config import OPENAI_API_KEY

if not OPENAI_API_KEY:
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
