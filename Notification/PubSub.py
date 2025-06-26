from paper_handling.paper_handler import fetch_works_multiple_queries
import logging
from chroma_db.chroma_vector_db import ChromaVectorDB
from llm.Embeddings import embed_string, embed_user_profile
from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


logger = logging.getLogger(__name__)

USER_QUERY = "I'm researching the application of Gaussian Process Bandits in optimizing machine learning tasks. Specifically, I'm interested in enhancing exploration-exploitation trade-offs and improving computational efficiency through GPU acceleration for large-scale experiments."
TRIGGER_DATE = "2024-01-01"

TAGS = [
    "Gaussian Process Bandits",
    "Bayesian Optimization",
    "Exploration-Exploitation Tradeoff",
    "GPU-Accelerated Machine Learning",
    "Scalable Machine Learning Algorithms"]
MAX_NUMBER_OF_SENT_MAIL = 2

db = ChromaVectorDB()


def add_papers_and_search_similar(
    papers: List[Dict[str, str]],
    user_query: str = USER_QUERY,
    k: int = 2
) -> Optional[List[str]]:
    """
    Fügt Paper-Titel in ChromaDB ein und führt anschließend eine Similarity-Suche mit der Nutzerbeschreibung durch.

    Args:
        papers (List[Dict[str, str]]): Liste von Papers mit 'id', 'title', 'user_description'
        k (int): Anzahl der Top-Ergebnisse

    Returns:
        Optional[List[str]]: Liste der ähnlichsten Paper-IDs
    """
    try:
        if not papers:
            logger.warning("Keine Papers übergeben.")
            return []

        # 1. Papers einfügen
        for paper in papers:
            try:
                paper_id = paper["id"]
                info = paper["info"]
                embedding = embed_string(info)

                db.collection.upsert(
                    ids=[paper_id],
                    embeddings=[embedding],
                    documents=[info],
                    metadatas=[{"source": "openalex"}]
                )
            except Exception as e:
                logger.error(f"Fehler beim Einfügen von Paper: {e}")

        # 2. Nutzerbeschreibung aus dem ersten Element ziehen
        user_description = user_query
        user_embedding = embed_string(user_description)

        # 3. Ähnlichkeitssuche
        similar_ids = db.perform_similarity_search(k=k, user_profile_embedding=user_embedding)
        return similar_ids

    except Exception as e:
        logger.error(f"Fehler in add_papers_and_search_similar: {e}")
        return None


def simplify_paper_results(papers: list[dict]) -> list[dict]:
    simplified = []

    for paper in papers:
        simplified.append({
            "hash": paper["id"].rstrip("/").split("/")[-1],
            "text": paper["title"] + paper["abstract"],
        })
    return simplified


def rank_and_filter_similar_papers(
    simplified_papers: list[dict],
    similarity_ids: list[str]
) -> list[dict]:

    id_to_paper = {paper["hash"]: paper for paper in simplified_papers}
    results = []

    for rank, id_ in enumerate(similarity_ids):
        if id_ in id_to_paper:
            paper = id_to_paper[id_].copy()
            paper["similarity_rank"] = rank
            results.append(paper)
    return results


def split_ranked_papers(
    result: list[dict],
    max_top_priority: int = MAX_NUMBER_OF_SENT_MAIL
) -> tuple[list[dict], list[dict]]:
    """
    Teilt die ranked result Liste in zwei Gruppen:
    - Liste A: Top-Papers mit Rank < 10, maximal max_top_priority Stück
    - Liste B: Restliche Papers mit Rank < 100

    Args:
        result: Liste von Paper-Dicts mit similarity_rank
        max_top_priority: maximale Anzahl in der Topliste (Rank < 10)

    Returns:
        (top_priority_list, rest_list)
    """
    top_priority = []
    rest = []

    for paper in result:
        rank = paper.get("similarity_rank")
        if rank is None or rank >= 100:
            continue  # ignorieren

        if rank < 5 and len(top_priority) < max_top_priority:
            top_priority.append(paper)
        else:
            rest.append(paper)

    return top_priority, rest


if __name__ == '__main__':
    # useless because we have it already in our pipline. it's just a hardcode
    temp = simplify_paper_results(fetch_works_multiple_queries(TAGS))
    # print(temp)
    db.store_embeddings(temp)  # fill db with papers
    # useless because we have it already in our pipline. it's just a hardcode
    temp = simplify_paper_results(fetch_works_multiple_queries(TAGS))
    # useless because we have it already in our pipline. it's just a hardcode
    new_papers = simplify_paper_results(fetch_works_multiple_queries(TAGS, TRIGGER_DATE))
    similar_ids = db.perform_similarity_search(k=150, user_profile_embedding=embed_user_profile(USER_QUERY))

    """
    similarity_ids = [
        "W005", "W0022", "W0092", "W0032", "W0012", "W015", "W002", "W007", "W011", "W008",
        "W014", "W012", "W017", "W029", "W026"
    ]
    # Top-5 Ergebnisse
    simplified_papers = [
        {"hash": "W001", "text": "Title 1 about Topic 1"},
        {"hash": "W002", "text": "Title 2 about Topic 2"},
        {"hash": "W003", "text": "Title 3 about Topic 3"},
        {"hash": "W004", "text": "Title 4 about Topic 4"},
        {"hash": "W005", "text": "Title 5 about Topic 5"},
        {"hash": "W006", "text": "Title 6 about Topic 6"},
        {"hash": "W007", "text": "Title 7 about Topic 7"},
        {"hash": "W008", "text": "Title 8 about Topic 8"},
        {"hash": "W009", "text": "Title 9 about Topic 9"},
        {"hash": "W010", "text": "Title 10 about Topic 10"},
        {"hash": "W011", "text": "Title 11 about Topic 11"},
        {"hash": "W012", "text": "Title 12 about Topic 12"},
        {"hash": "W013", "text": "Title 13 about Topic 13"},
        {"hash": "W014", "text": "Title 14 about Topic 14"},
        {"hash": "W015", "text": "Title 15 about Topic 15"},
        {"hash": "W016", "text": "Title 16 about Topic 16"},
        {"hash": "W017", "text": "Title 17 about Topic 17"},
        {"hash": "W018", "text": "Title 18 about Topic 18"},
        {"hash": "W019", "text": "Title 19 about Topic 19"},
        {"hash": "W020", "text": "Title 20 about Topic 20"},
    ]
    """
    results = rank_and_filter_similar_papers(new_papers, similar_ids)
    email, ui = split_ranked_papers(results, MAX_NUMBER_OF_SENT_MAIL)
    print(email)
    print("***********")
    print(ui)
