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
import os

from pydantic_ai import Embedder
from pydantic_ai.embeddings import TestEmbeddingModel

from llm.LLMDefinition import LLM

logger = logging.getLogger(__name__)


TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

# Optional OpenAI-compatible client (used by tests and for backward compatibility)
client = None

if TEST_MODE:
    embedder = Embedder(TestEmbeddingModel())
else:
    embedder = Embedder(f"openai:{EMBEDDING_MODEL}")


async def embed_string(text: str) -> list[float]:
    """
    Embed a string using the configured embedder.
    Args:
        text (str): The text to embed.
    Returns:
        list[float]: The embedding vector.
    """
    text = text.replace("\n", " ")

    if client is not None and hasattr(client, "embeddings"):
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
        if asyncio.iscoroutine(response):
            response = await response
        data = getattr(response, "data", None)
        if data:
            first = data[0]
            embedding = getattr(first, "embedding", None)
            if embedding is None and isinstance(first, dict):
                embedding = first.get("embedding")
            if embedding is not None:
                return list(embedding)

    result = await embedder.embed_documents([text])
    return result.embeddings[0]


async def embed_user_profile(text):
    """
    Embed user profile text, summarizing if too long.
    Args:
        text (str): The user profile text.
    Returns:
        list[float]: The embedding vector.
    """
    return await embed_paper_text(text)


async def embed_papers(title, abstract):
    """
    Embed a paper by concatenating its title and abstract.
    Args:
        title (str): The paper title.
        abstract (str): The paper abstract.
    Returns:
        list[float]: The embedding vector.
    """
    return await embed_string(title + abstract)


async def embed_paper_text(paper_text: str) -> list[float]:
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
        return await embed_string(paper_text)

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

    response = LLM(prompt)
    if asyncio.iscoroutine(response):
        response = await response
    summary = str(response.content).strip()
    logger.info("Generated summary: " + summary)

    return await embed_string(summary)
