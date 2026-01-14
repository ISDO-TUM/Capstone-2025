"""
Embedding utilities for the Capstone project.

Responsibilities:
- Provides functions to embed user profiles, paper titles/abstracts, and arbitrary text
- Handles summarization of long texts before embedding
- Uses OpenAI embedding models and the LLM for summarization
- Used throughout the agent and ingestion flows for vector search and ranking
"""

import logging
from openai import OpenAI
from llm.LLMDefinition import OPENAI_API_KEY, LLM, TEST_MODE

# Use mock client in TEST_MODE to avoid real API calls
if TEST_MODE:
    from unittest.mock import MagicMock

    client = MagicMock()
    # Mock embeddings.create to return standard 1536-dim vector
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
    client.embeddings.create.return_value = mock_response
else:
    client = OpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)


def embed_string(text, model="text-embedding-3-small"):
    """
    Embed a string using the specified OpenAI embedding model.
    Args:
        text (str): The text to embed.
        model (str): The embedding model to use (default: 'text-embedding-3-small').
    Returns:
        list[float]: The embedding vector.
    """
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding


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

    response = LLM.invoke(prompt)
    summary = str(response.content).strip()
    logger.info("Generated summary: " + summary)

    return embed_string(summary)
