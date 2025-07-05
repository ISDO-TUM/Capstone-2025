import re

from pyalex import Works
from utils.status import Status


def _fetch_works_single_query(query, from_publication_date=None):
    """
    Fetch works from OpenAlex matching a query.

    Parameters:
    - query (str): Search keyword or phrase.
    - from_publication_date (str, optional): Filter works published on or after this date (YYYY-MM-DD format).

    Returns:
    - List[dict]: Each dict contains id, title, abstract, authors, publication_date, landing_page_url, pdf_url.
    """
    try:
        works_query = (
            Works()
            .select(
                "id,title,abstract_inverted_index,authorships,publication_date,primary_location,"
                "citation_normalized_percentile,fwci,cited_by_count,counts_by_year,topics, relevance_score"
            )
            .search(query)
            .sort(relevance_score="desc")
        )
        if from_publication_date:
            works_query = works_query.filter(from_publication_date=from_publication_date)
        works = works_query.get(per_page=5)
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
            authors = ", ".join([
                a["author"]["display_name"] for a in authorships
            ])

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

            results.append({
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
                "pdf_url": pdf_url
            })
        except Exception as ex:
            print(f"Error processing work '{work.get('id', 'unknown')}': {ex}")
            continue

    return results, Status.SUCCESS


def fetch_works_multiple_queries(queries, from_publication_date=None):
    """
    This function takes a list of search queries and retrieves scientific papers from the OpenAlex API
    for each query. It returns a single flattened list of dictionaries, each representing one paper.

    Each dictionary includes the following fields:
    - id: OpenAlex ID of the paper
    - title: Title of the paper
    - abstract: Abstract text reconstructed from the inverted index
    - authors: A comma-separated list of author names
    - publication_date: Date of publication
    - landing_page_url: URL to the paper's landing page
    - pdf_url: Direct URL to the PDF, if available
    - similarity_score: OpenAlex relevance_score (float) – renamed for clarity
    - fwci: Field-Weighted Citation Impact (float or None)
    - citation_normalized_percentile: Citation percentile within field/year (float or None)
    - cited_by_count: Raw citation count (int or None)
    - counts_by_year: Year-by-year citation breakdown (list of dicts or None)

    Parameters:
    - queries (List[str]): Search keywords or phrases.
    - from_publication_date (str, optional): Filter works published on or after this
      date (YYYY-MM-DD).

    Returns:
    - Tuple[List[dict], int]: A tuple containing:
        • A combined list of work-metadata dictionaries (schema above)
        • Status code (Status.SUCCESS if all queries succeeded, Status.FAILURE if any failed)
    """
    all_works = []
    any_failure = False
    for query in queries:
        try:
            works, status = _fetch_works_single_query(query, from_publication_date)
            all_works.extend(works)
            if status == Status.FAILURE:
                any_failure = True
        except Exception as e:
            print(f"Error fetching works for query '{query}': {e}")
            any_failure = True
    return all_works, Status.FAILURE if any_failure else Status.SUCCESS


def clean_topics_field(topics: list[dict]) -> list[dict]:
    """
    Cleans a list of OpenAlex topic dictionaries for prompt-efficient use by an agent.
    Handles multiple subfields/fields/domains per topic if they exist as lists.

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
            "domains": get_names(topic.get("domain"))
        }
        cleaned.append(cleaned_entry)
    return cleaned


def is_valid_abstract(text, min_words=50, max_words=500):
    lower_text = text.lower()
    word_count = len(text.split())

    # Reject if too short or too long
    if word_count < min_words or word_count > max_words:
        return False

    # Reject if it contains obvious non-abstract elements
    spam_indicators = [
        "previous article", "next article",
        "google scholar", "crossref", "bibtex",
        "https://doi.org", "add to favorites", "export citation"
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


if __name__ == "__main__":
    print(fetch_works_multiple_queries(["biomedical", "LLMs"], "2025-06-01"))
