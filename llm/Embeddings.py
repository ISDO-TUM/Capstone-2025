import logging
from openai import OpenAI
from llm.LLMDefinition import OPENAI_API_KEY, LLM
from langchain_core.messages import HumanMessage

client = OpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)


def embed_string(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding


def embed_user_profile(text):
    """Embed user profile text, summarize if it's too long."""
    return embed_paper_text(text)


def embed_papers(title, abstract):
    return embed_string(title + abstract)


def embed_paper_text(paper_text: str) -> list[float]:
    """Embed paper text, summarize if it's too long."""
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

    response = LLM.invoke([HumanMessage(content=prompt)])
    summary = str(response.content).strip()
    logger.info("Generated summary: " + summary)

    return embed_string(summary)
