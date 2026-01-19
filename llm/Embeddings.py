"""
Embedding utilities for the Capstone project.

Responsibilities:
- Provides functions to embed user profiles, paper titles/abstracts, and arbitrary text
- Handles summarization of long texts before embedding
- Uses OpenAI embedding models and the LLM for summarization
- Used throughout the agent and ingestion flows for vector search and ranking
"""

from __future__ import annotations

import asyncio
import logging
from typing import List

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from llm.LLMDefinition import OPENAI_API_KEY, LLM

logger = logging.getLogger(__name__)


class EmbeddingResponse(BaseModel):
    vector: List[float]


EmbeddingAgent = Agent(
    model=OpenAIModel(
        model_name="text-embedding-3-small",
        api_key=OPENAI_API_KEY,
    ),
    result_type=EmbeddingResponse,
)


def embed_string(text: str) -> list[float]:
    """
    Embed a string using the specified EmbeddingAgent.
    Args:
        text (str): The text to embed.
    Returns:
        list[float]: The embedding vector.
    """
    text = text.replace("\n", " ")

    async def _embed():
        result = await EmbeddingAgent.run(text)
        return result.data.vector

    return asyncio.run(_embed())


def embed_user_profile(text):
    """
    Embed user profile text, summarizing if too long.
    Args:
        text (str): The user profile text.
    Returns:
        list[float]: The embedding vector.
    """
    return embed_paper_text(text)


def embed_papers(title, abstract):
    """
    Embed a paper by concatenating its title and abstract.
    Args:
        title (str): The paper title.
        abstract (str): The paper abstract.
    Returns:
        list[float]: The embedding vector.
    """
    return embed_string(title + abstract)


def embed_paper_text(paper_text: str) -> list[float]:
    """
    Embed paper text, summarizing if too long for the embedding model.
    Args:
        paper_text (str): The full paper text.
    Returns:
        list[float]: The embedding vector.
    Side effects:
        Calls the LLM to summarize if the text exceeds 1500 words.
    """
    if not paper_text or not paper_text.strip():
        return []

    word_count = len(paper_text.split())

    if word_count <= 1500:
        logger.info("Length within limit, embedding right away...")
        return embed_string(paper_text)

    # Summarize if too long
    logger.info("Length over limit, summarizing...")
    prompt = f"""Write a clear, academic-style summary (300–400 words) of the following research paper for the purpose of building a user profile.
    Focus on the problem the paper addresses, the main approach or methodology, the key contributions or findings, and the impact or significance of the work.
    Integrate these elements into a seamless, coherent narrative.
    Do not include author lists, copyright notices, or technical details that do not contribute to understanding the core research.

    Paper text:
    {paper_text}

    Summary:
    """

    response = asyncio.run(LLM(prompt))
    summary = str(response.content).strip()
    logger.info("Generated summary: " + summary)

    return embed_string(summary)
