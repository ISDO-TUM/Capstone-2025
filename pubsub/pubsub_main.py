import logging
from datetime import datetime, timedelta

import chromadb
import numpy as np
from chromadb.api.models.Collection import Collection
from utils.status import Status
from typing import List, Optional, TypedDict
from database.papers_database_handler import insert_papers
from database.projects_database_handler import get_queries_for_project, get_project_prompt
import ast

from llm.Embeddings import embed_papers
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
    # status_postgres, papers = insert_papers(papers)

    # Insert papers in chroma
    # status_chroma = embed_papers(papers)

    # Get project prompt
    project_prompt = get_project_prompt(project_id)
    print(f"Project prompt: {project_prompt}")

    # todo store project prompt embedding together with project
    # Embed project prompt

    # Perform similarity search between latest papers and user query, get top k
    sorted_sims = _sim_search(papers, project_prompt)
    top_results = sorted_sims[:3]
    # Get current papers with newsletter tag and unseen tag
    # Make agent decide a subset of top k latest papers and current news, set subset as new newsletter papers
    # Determine different papers between old newsletter papers and new newsletter papers
    # Send difference per mail


def _embed_and_store(deduplicated_papers):
    embedded_papers = []
    for paper in deduplicated_papers:
        embedding = embed_papers(paper['title'],
                                 paper['abstract'])
        embedded_paper = {
            'embedding': embedding,
            'hash': paper['hash'],
        }
        embedded_papers.append(embedded_paper)

    return chroma_db.store_embeddings(embedded_papers)


def _sim_search(papers, project_vector):
    hashes = []
    for paper in papers:
        hashes.append(paper['hash'])
    latest_papers_subset = chroma_db.collection.get(ids=hashes)
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


if __name__ == '__main__':
    update_newsletter_papers("aaefbb83-47a5-4606-9026-d15cad897b10")
