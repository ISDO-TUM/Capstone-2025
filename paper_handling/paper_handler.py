"""
OpenAlex API and paper metadata utilities for the Capstone project.

Responsibilities:
- Fetches and processes papers from OpenAlex based on queries
- Cleans and validates paper metadata for ingestion and recommendation
- Provides utilities for searching, filtering, and summarizing papers
- Used throughout the agent and ingestion flows for paper retrieval and processing
"""

import re

from pyalex import Works

from database.papers_database_handler import get_papers_by_hash
from database.projectpaper_database_handler import assign_paper_to_project
from llm.LLMDefinition import LLM
from utils.status import Status
import logging

logger = logging.getLogger(__name__)


def _fetch_works_single_query(query, from_publication_date=None, per_page=10):
    """
    Fetch works from OpenAlex matching a query.
    Args:
        query (str): Search keyword or phrase.
        from_publication_date (str, optional): Filter works published on or after this date (YYYY-MM-DD format).
        per_page (int): Number of papers to fetch per query (default: 10).
    Returns:
        list[dict]: List of paper metadata dicts.
        int: Status.SUCCESS if successful, Status.FAILURE otherwise.
    """
    try:
        works_query = (
            Works()
            .select(
                "id,title,abstract_inverted_index,authorships,publication_date,primary_location,citation_normalized_percentile,fwci,cited_by_count,counts_by_year,topics, relevance_score"
            )
            .search(query)
            .sort(relevance_score="desc")
        )
        if from_publication_date:
            works_query = works_query.filter(
                from_publication_date=from_publication_date
            )
        works = works_query.get(per_page=per_page)
    except Exception as e:
        print(f"Error fetching works for query '{query}': {e}")
        return [], Status.FAILURE

    results = []
    for work in works:
        try:
            work_id = work.get("id")
            title = work.get("title")

            # Reconstruct abstract from inverted index
            abstract_idx = work.get("abstract_inverted_index")
            if abstract_idx:
                index_map = {v: k for k, values in abstract_idx.items() for v in values}
                abstract = " ".join(index_map[i] for i in sorted(index_map))
                if not is_valid_abstract(abstract):
                    abstract = "No abstract available"
            else:
                abstract = "No abstract available"

            # Extract authors as a comma-separated string
            authorships = work.get("authorships", [])
            authors = ", ".join([a["author"]["display_name"] for a in authorships])

            # Extract URLs
            primary_location = work.get("primary_location", {})
            landing_page_url = primary_location.get("landing_page_url")
            pdf_url = primary_location.get("pdf_url")

            publication_date = work.get("publication_date")

            relevance = work.get("relevance_score")
            citation_normalized_percentile = work.get("citation_normalized_percentile")
            fwci = work.get("fwci")
            cited_by_count = work.get("cited_by_count")
            counts_by_year = work.get("counts_by_year")

            topics = clean_topics_field(work.get("topics"))

            results.append(
                {
                    "id": work_id,
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "publication_date": publication_date,
                    "fwci": fwci,
                    "citation_normalized_percentile": citation_normalized_percentile,
                    "cited_by_count": cited_by_count,
                    "counts_by_year": counts_by_year,
                    "topics": topics,
                    "landing_page_url": landing_page_url,
                    "similarity_score": relevance,
                    "pdf_url": pdf_url,
                }
            )
        except Exception as ex:
            print(f"Error processing work '{work.get('id', 'unknown')}': {ex}")
            continue

    return results, Status.SUCCESS


def fetch_works_multiple_queries(queries, from_publication_date=None, per_page=10):
    """
    Fetch papers from OpenAlex for a list of queries, returning a flattened list of paper metadata dicts.
    Args:
        queries (list[str]): Search keywords or phrases.
        from_publication_date (str, optional): Filter works published on or after this date (YYYY-MM-DD).
        per_page (int): Number of papers to fetch per query (default: 10).
    Returns:
        tuple: (list[dict], int) - List of paper metadata dicts, status code.
    """
    all_works = []
    any_failure = False
    for query in queries:
        try:
            works, status = _fetch_works_single_query(
                query, from_publication_date, per_page
            )
            all_works.extend(works)
            if status == Status.FAILURE:
                any_failure = True
        except Exception as e:
            print(f"Error fetching works for query '{query}': {e}")
            any_failure = True
    logger.info(f"Fetched {len(all_works)} papers")
    return all_works, Status.FAILURE if any_failure else Status.SUCCESS


def clean_topics_field(topics: list[dict]) -> list[dict]:
    """
    Clean a list of OpenAlex topic dictionaries for prompt-efficient use by an agent.
    Args:
        topics (list[dict]): Original list of topic entries from OpenAlex.
    Returns:
        list[dict]: Cleaned list of topic information.
    """

    def get_names(entry):
        if isinstance(entry, list):
            return [e.get("display_name") for e in entry if "display_name" in e]
        elif isinstance(entry, dict):
            return [entry.get("display_name")]
        else:
            return []

    cleaned = []
    for topic in topics:
        cleaned_entry = {
            "topic": topic.get("display_name"),
            "score": topic.get("score"),
            "subfields": get_names(topic.get("subfield")),
            "fields": get_names(topic.get("field")),
            "domains": get_names(topic.get("domain")),
        }
        cleaned.append(cleaned_entry)
    return cleaned


def is_valid_abstract(text, min_words=50, max_words=500):
    """
    Validate if a text is a plausible scientific abstract.
    Args:
        text (str): The abstract text to validate.
        min_words (int): Minimum word count.
        max_words (int): Maximum word count.
    Returns:
        bool: True if valid, False otherwise.
    """
    lower_text = text.lower()
    word_count = len(text.split())

    # Reject if too short or too long
    if word_count < min_words or word_count > max_words:
        return False

    # Reject if it contains obvious non-abstract elements
    spam_indicators = [
        "previous article",
        "next article",
        "google scholar",
        "crossref",
        "bibtex",
        "https://doi.org",
        "add to favorites",
        "export citation",
    ]
    if any(indicator in lower_text for indicator in spam_indicators):
        return False

    # Reject if it contains many citation-style references like "[1]" or "[2]"
    if len(re.findall(r"\[\d+\]", text)) > 5:
        return False

    # Reject if there are too few sentence-ending punctuations
    sentence_endings = len(re.findall(r"[.!?]", text))
    if sentence_endings < 3:
        return False

    return True


def search_and_filter_papers(
    chroma_db, user_profile_embedding, current_paper_hashes, min_similarity=0.3
):
    """
    Search for papers using vector similarity and filter out already shown ones.
    Args:
        chroma_db: ChromaVectorDB instance.
        user_profile_embedding (list[float]): User profile embedding vector.
        current_paper_hashes (set): Hashes of already shown papers.
        min_similarity (float): Minimum similarity threshold.
    Returns:
        list[dict]: List of available paper metadata dicts.
    """
    candidate_result = chroma_db.perform_similarity_search(
        1000, user_profile_embedding, return_scores=True, min_similarity=min_similarity
    )

    if not candidate_result:
        return []

    candidate_hashes, similarity_scores = candidate_result
    print(
        f"ChromaDB returned {len(candidate_hashes)} candidate hashes with similarity >= {min_similarity}"
    )
    all_papers = get_papers_by_hash(candidate_hashes)

    # Filter out already shown papers and take first 10
    available_papers = []
    for paper in all_papers:
        if paper.get("paper_hash") not in current_paper_hashes:
            available_papers.append(paper)
            if len(available_papers) >= 10:
                break

    return available_papers


def generate_paper_summary(paper, project_description):
    """
    Generate a summary for a paper explaining its relevance to the project.
    Args:
        paper (dict): Paper metadata dict.
        project_description (str): The user's research interests or project description.
    Returns:
        str: Concise summary of the paper's relevance.
    """
    summary_prompt = f"""
    Generate a concise summary explaining why this paper is relevant to the user's research interests.

    User's research interests: {project_description}
    Paper title: {paper.get("title", "Unknown")}
    Paper abstract: {paper.get("abstract", "No abstract available")}

    Write a brief summary (2 short sentences).
    """
    try:
        summary_response = LLM.invoke(summary_prompt)
        if hasattr(summary_response, "content"):
            content = summary_response.content
            summary = (
                content.strip() if isinstance(content, str) else str(content).strip()
            )
        else:
            summary = str(summary_response).strip()
        if not summary:
            summary = "Relevant based on user interests."
    except Exception:
        summary = "Relevant based on user interests."
    return summary


def create_paper_dict(paper, summary):
    """
    Create a standardized paper dictionary for frontend consumption.
    Args:
        paper (dict): Paper metadata dict.
        summary (str): Relevance summary.
    Returns:
        dict: Standardized paper dict with title, link, description, hash, and is_replacement.
    """
    return {
        "title": paper.get("title", "N/A"),
        "link": paper.get("landing_page_url", "N/A"),
        "description": summary,
        "hash": paper["paper_hash"],
        "is_replacement": False,
    }


def process_available_papers(
    available_papers, project_id, project_description, max_papers=10
):
    """
    Process available papers and return recommendations, storing them for the project.
    Args:
        available_papers (list[dict]): List of available paper metadata dicts.
        project_id (str): The project ID.
        project_description (str): The user's research interests or project description.
        max_papers (int): Maximum number of papers to process (default: 10).
    Returns:
        list[dict]: List of standardized paper dicts for recommendations.
    Side effects:
        Stores each recommended paper for the project in the database.
    """
    if not available_papers:
        return []

    new_recommendations = []
    for paper in available_papers[:max_papers]:
        summary = generate_paper_summary(paper, project_description)
        assign_paper_to_project(paper["paper_hash"], project_id, summary)
        paper_dict = create_paper_dict(paper, summary)
        new_recommendations.append(paper_dict)

    return new_recommendations


# NOTE: This block is for local testing only. Uncomment to run local tests.
# if __name__ == "__main__":
#     print(fetch_works_multiple_queries(["biomedical", "LLMs"], "2025-06-01"))
