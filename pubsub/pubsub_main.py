import json
import logging
from datetime import datetime, timedelta

import chromadb
import numpy as np
from chromadb.api.models.Collection import Collection

from database.projectpaper_database_handler import get_pubsub_papers_for_project
from utils.status import Status
from typing import List, TypedDict
from database.papers_database_handler import insert_papers, get_papers_by_original_id
from database.projects_database_handler import get_queries_for_project, get_project_prompt
import ast

from llm.Embeddings import embed_papers, embed_user_profile
from paper_handling.paper_handler import fetch_works_multiple_queries

logger = logging.getLogger(__name__)


class PaperData(TypedDict):
    embedding: List[float]
    hash: str


class ChromaVectorDB:
    def __init__(self, collection_name: str = "research-papers", outside_docker=False) -> None:
        # UNCOMMENT THIS FOR LOCAL TESTING ONLY;
        if outside_docker:
            self.client = chromadb.HttpClient(host="localhost", port=8000)
        # THIS SHOULD BE USED IN PRODUCTION
        else:
            self.client = chromadb.HttpClient(host="chromadb", port=8000)
        self.collection: Collection = self.client.get_or_create_collection(collection_name)

    def store_embeddings(self, data: List[PaperData]) -> int:
        """
        Store text embeddings in Chroma using OpenAI API.

        Args:
            data: list of dicts like {"hash": str, "embedding": List[float]}

        Returns:
            status_code: Status.SUCCESS if all succeeded, Status.FAILURE if any failed
        """
        any_failure = False

        for item in data:
            try:
                hash_id = item["hash"]
                embedding = item["embedding"]
                print(f"Storing embedding: {embedding} for hash: {hash_id}")
                self.collection.upsert(
                    ids=[hash_id],
                    embeddings=[embedding],
                )

            except Exception as e:
                logger.error(f"Failed to store embedding for hash={item.get('hash')}: {e}")
                any_failure = True

        return Status.FAILURE if any_failure else Status.SUCCESS


chroma_db = ChromaVectorDB(outside_docker=True)


def start_pubsub():
    # todo call update newsletter papers periodically
    pass


def _one_week_ago_date():
    one_week_ago = datetime.today() - timedelta(weeks=1)
    return one_week_ago.strftime("%Y-%m-%d")


def update_newsletter_papers(project_id: str):
    k = 3
    # Get queries for project
    queries_str = get_queries_for_project(project_id)[0]
    print(queries_str)
    queries = ast.literal_eval(queries_str)
    # Get papers from last week
    papers, _ = fetch_works_multiple_queries(queries, from_publication_date="2020-01-01")

    # Insert papers in postgres
    insert_papers(papers)

    papers_w_hash = []
    for paper in papers:
        papers_w_hash.append(get_papers_by_original_id(paper['id'])[0])  # For now, we only use a single version of the paper
    papers_w_hash = _remove_duplicate_dicts(papers_w_hash)
    print(f"papers with hash: {papers_w_hash}")
    # Insert papers in chroma
    _embed_and_store(papers_w_hash)

    # Get project prompt
    project_prompt = get_project_prompt(project_id)[0]
    print(f"Project prompt: {project_prompt}")

    # todo store project prompt embedding together with project
    # Embed project prompt
    embedded_prompt = embed_user_profile(project_prompt)
    # Perform similarity search between latest papers and user query, get top k
    sorted_sims = _sim_search(papers_w_hash, embedded_prompt)
    top_results = sorted_sims[:k]
    # Get current papers with newsletter tag and unseen tag
    current_newsletter_papers = get_pubsub_papers_for_project(project_id)

    print(f"Current newsletter papers: {current_newsletter_papers}")
    print(top_results)
    # Link hashes to actual papers
    # Make agent decide a subset of top k latest papers and current news, set subset as new newsletter papers
    # Determine different papers between old newsletter papers and new newsletter papers
    # Send difference per mail


def _embed_and_store(papers):
    embedded_papers = []
    for paper in papers:
        embedding = embed_papers(paper['title'],
                                 paper['abstract'])
        embedded_paper = {
            'embedding': embedding,
            'hash': paper['paper_hash'],
        }
        embedded_papers.append(embedded_paper)

    return chroma_db.store_embeddings(embedded_papers)


def _sim_search(papers, project_vector):
    hashes = []
    for paper in papers:
        hashes.append(paper['paper_hash'])
    latest_papers_subset = chroma_db.collection.get(ids=hashes, include=['embeddings'])
    print(latest_papers_subset)
    results = []
    for id, embedding in zip(latest_papers_subset["ids"], latest_papers_subset["embeddings"]):
        sim = _cosine_similarity(project_vector, embedding)
        results.append((id, sim))
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def _cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def _remove_duplicate_dicts(dict_list):
    """
    Removes duplicate dictionaries from a list based on their content.

    Args:
        dict_list (list): List of dictionaries.

    Returns:
        list: New list with duplicates removed.
    """
    seen = set()
    unique_list = []
    for d in dict_list:
        key = json.dumps(d, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique_list.append(d)
    return unique_list


if __name__ == '__main__':
    update_newsletter_papers("044c3e5d-ec24-4664-8967-e1d64fcfd276")
