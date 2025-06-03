from typing import Any

from langchain_core.tools import tool

from chroma_db import store_embeddings
from chroma_db.chroma_vector_db import chroma_db
from llm.Embeddings import embed_papers
from paper_handling.database_handler import insert_papers
from paper_handling.paper_handler import fetch_works_multiple_queries


@tool
def update_papers(queries: list[str]) -> str:
    """
    Tool Name: update_papers
    Description:
        This tool updates the paper database with the latest research papers and their embeddings
        based on a list of keyword search queries. It performs the following steps:
        1. Fetches new papers using the provided list of keyword queries.
        2. Stores the fetched papers in a PostgreSQL database, removing any duplicates.
        3. Computes and stores embeddings for the newly stored papers.
    Use Case:
        Use this tool when you want to refresh the paper database with the latest research and ensure
        that all relevant papers have updated embeddings for ranking or similarity comparison tasks.
    Input:
        queries (list[str]): A list of keyword strings to search for relevant papers.
    Output:
        A status message string indicating whether the process completed successfully without errors,
        or completed with some errors that can be ignored.
    Returns:
        str: A human-readable summary of the update operation's result.
    """
    try:
        # Step 1: Fetch works from multiple queries
        downloaded_papers, status_download = fetch_works_multiple_queries(queries)

        # Step 2: Store works in Postgres
        status_db, deduplicated_papers = insert_papers(downloaded_papers)

        embedding_dicts = []
        # Step 3.1: Embed papers
        for paper in deduplicated_papers:
            embedding = embed_papers(deduplicated_papers['title'],
                                     deduplicated_papers['abstract'])
            embedding_dict = {
                'embedding': embedding,
                'hash': paper['hash'],
            }
            embedding_dicts.append(embedding_dict)

        # Step 3.2: Store papers in chroma
        status_chroma = chroma_db.store_embeddings(embedding_dicts)

        # Check if all status codes are 0
        if status_download == 0 and status_db == 0 and status_chroma == 0:
            return ("Paper database has been updated with the latest papers & embeddings. There were no errors. "
                    "Now you can rank the papers.")
        else:
            return ("Paper database has been updated with the latest papers & embeddings. There were some errors. "
                    "Ignore the errors and proceed with ranking the papers.")

    except Exception as e:
        print(f"An error occurred in update_papers: {e}")
        return ("Paper database has been updated with the latest papers & embeddings. There were some errors. "
                "Ignore the errors and proceed with ranking the papers.")

# DEPRECATED


def get_paper_basic_data(queries: list[str]) -> list[dict[str, Any]]:
    """
    This function takes a list of queries and returns a list of paper titles.
    Args:
        queries: A list of queries in form of string keywords corresponding to the user's interests.
        each query corresponds to a different interest field. Like: ['generative models', 'renewable energies', ...]
    Example input:
    {
      "queries": ["agriculture in Costa Rica", "Use of pesticides in central America", ...],
    }
    Returns:
        A list of paper data (title, link) with corresponding to papers related to all the queries.
    """
    paper_metadata = fetch_works_multiple_queries(queries)
    paper_titles = [work["title"] for work in paper_metadata]
    paper_links = [_get_link(work) for work in paper_metadata]

    paper_basic_data = [{'title': title, 'link': link} for title, link in zip(paper_titles, paper_links)]
    return paper_basic_data


def _get_link(work):
    """
    This function takes a paper work object and returns its link
    Args:
        work: an open alex work object

    Returns: the link of the work either doi, oa_url, open alex url or None.

    """
    link = work.get('doi')
    if not link:
        link = work.get('open_access', {}).get('oa_url')
    if not link:
        link = work.get('landing_page_url')
    if not link:
        if work.get('id') and work.get('id').startswith('http'):
            link = work.get('id')
        else:
            link = "#"
    return link
