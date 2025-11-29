import json
import logging
from datetime import datetime, timedelta, timezone
from chroma_db.chroma_vector_db import chroma_db
import numpy as np
from database.projectpaper_database_handler import (
    get_pubsub_papers_for_project,
    reset_newsletter_tags,
    set_newsletter_tags_for_project,
)
from pubsub import pubsub_params

from pubsub.temporary_llm_that_will_be_replaced_soon import calL_temp_agent
from typing import List, TypedDict
from database.papers_database_handler import (
    insert_papers,
    get_papers_by_original_id,
    get_paper_by_hash,
)
from database.projects_database_handler import (
    get_queries_for_project,
    get_project_prompt,
    get_user_profile_embedding,
    get_project_owner_id,
)
import ast
from llm.Embeddings import embed_papers
from paper_handling.paper_handler import fetch_works_multiple_queries

logger = logging.getLogger(__name__)


class PaperData(TypedDict):
    embedding: List[float]
    hash: str


def _one_week_ago_date():
    one_week_ago = datetime.today() - timedelta(weeks=1)
    return one_week_ago.strftime("%Y-%m-%d")


def update_newsletter_papers(project_id: str):
    k = 3
    logger.info(f"[update_newsletter_papers] START for project {project_id}")

    owner_id = get_project_owner_id(project_id)
    if not owner_id:
        logger.error(
            f"[update_newsletter_papers] Unable to determine owner for project {project_id}"
        )
        return

    # 1. Get queries for project
    logger.info("  ↳ fetching queries for project…")
    qs = get_queries_for_project(owner_id, project_id)
    if not qs:
        logger.error(f"  ✖ no queries found for project {project_id}")
        return
    queries_str = qs[0]
    queries = ast.literal_eval(queries_str)
    logger.info(f"    ✓ queries: {queries}")

    # Get prompt + embedded prompt
    logger.info("  ↳ fetching project prompt…")
    pp = get_project_prompt(owner_id, project_id)
    if not pp:
        logger.error(f"    ✖ no prompt found for project {project_id}")
        return
    project_prompt = pp[0]
    logger.info(f"    ✓ prompt: {project_prompt[:50]}…")

    logger.info("  ↳ querying embedded project prompt…")
    embedded_prompt = get_user_profile_embedding(
        owner_id, project_id
    )  # todo handle cases where this is null
    logger.info("    ✓ prompt embedding acquired")

    # 2. Fetch works
    logger.info("  ↳ fetching works from API…")
    papers, _ = fetch_works_multiple_queries(
        queries, from_publication_date=get_update_date(pubsub_params.DAYS_FOR_UPDATE)
    )
    logger.info(f"    ✓ fetched {len(papers)} papers")

    # 3. Insert into Postgres
    logger.info("  ↳ inserting papers into Postgres…")
    insert_papers(papers)
    logger.info("    ✓ insert complete")

    # 4. Resolve hashes
    logger.info("  ↳ resolving paper hashes…")
    papers_w_hash = []
    for paper in papers:
        p = get_papers_by_original_id(paper["id"])
        if not p:
            logger.warning(f"    ⚠ no DB record for original id {paper['id']}")
            continue
        papers_w_hash.append(p[0])
    papers_w_hash = _remove_duplicate_dicts(papers_w_hash)
    logger.info(f"    ✓ {len(papers_w_hash)} unique hashed papers")

    # 5. Embed & store in Chroma
    logger.info("  ↳ embedding & upserting into Chroma…")
    _embed_and_store(papers_w_hash)
    logger.info("    ✓ chroma upsert complete")

    # 6. Similarity search
    logger.info(f"  ↳ running similarity search (top {k})…")
    sims = _sim_search(papers_w_hash, embedded_prompt)
    top_results = sims[:k]
    logger.info(f"    ✓ top results: {top_results}")

    # 7. Collect current + new candidates
    logger.info("  ↳ loading current newsletter-paper hashes…")

    # todo for now this returns all newsletter papers, not the old ones (older than update days threshold) that have not been seen
    current = get_pubsub_papers_for_project(
        project_id
    )  # If recommendation is older than the update days threshold but the user has not seen it consider it again

    logger.info(f"    ✓ {len(current)} existing newsletter entries")
    potential = []
    for h in current:
        potential.append(get_paper_by_hash(h[0]))
    for rid, _score in top_results:
        potential.append(get_paper_by_hash(rid))
    logger.info(f"    ✓ total candidates: {len(potential)}")

    # 8. Call agent
    logger.info("  ↳ calling LLM agent to pick+summarize…")
    agent_out = calL_temp_agent(str(potential), project_prompt, str(k)).content
    logger.info(f"    ✓ raw agent output: {agent_out}")
    agent_response = ast.literal_eval(agent_out)

    recommendation_hashes = []
    summaries = []

    # 9. Persist newsletter tags
    logger.info("  ↳ resetting old tags…")
    reset_newsletter_tags(project_id)
    logger.info("  ↳ setting new newsletter tags…")

    for item in agent_response:
        recommendation_hashes.append(item["paper_hash"])
        summaries.append(item["summary"])
        logger.info(f"      ▪ picked {item['paper_hash']}: {item['summary'][:40]}…")

    if not recommendation_hashes:
        logger.info(
            f"[update_newsletter_papers] No new recommendations for project {project_id}, skipping tag update"
        )
        return  # <-- without error, shows 200 OK
    set_newsletter_tags_for_project(
        project_id, paper_hashes=recommendation_hashes, summaries=summaries
    )
    logger.info(f"[update_newsletter_papers] DONE for project {project_id}")


def _embed_and_store(papers):
    embedded_papers = []
    for paper in papers:
        embedding = embed_papers(paper["title"], paper["abstract"])
        embedded_paper = {
            "embedding": embedding,
            "hash": paper["paper_hash"],
        }
        embedded_papers.append(embedded_paper)

    return chroma_db.store_embeddings(embedded_papers)


def _sim_search(papers, project_vector):
    hashes = []
    for paper in papers:
        hashes.append(paper["paper_hash"])
    latest_papers_subset = chroma_db.collection.get(ids=hashes, include=["embeddings"])
    results = []
    for id, embedding in zip(
        latest_papers_subset["ids"], latest_papers_subset["embeddings"]
    ):
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


def get_update_date(days_for_update: int | float) -> str:
    """
    Return the date (YYYY-MM-DD) for 'today minus days_for_update' in UTC.

    Parameters
    ----------
    days_for_update : int | float
        Number of days to subtract from the current date.

    Returns
    -------
    str
        The date string, e.g. '2025-07-05'.
    """
    target_date = (datetime.now(timezone.utc) - timedelta(days=days_for_update)).date()
    return target_date.isoformat()


# NOTE: This block is for local testing only. Uncomment to run local tests.
# if __name__ == '__main__':
# update_newsletter_papers("babbab43-0323-423e-ba29-f74ec07e2d57")
