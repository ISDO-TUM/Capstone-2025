from pyalex import Works


def _fetch_works_single_query(query):
    """
    Fetch works from OpenAlex matching a query.

    Parameters:
    - query (str): Search keyword or phrase.

    Returns:
    - List[dict]: Each dict contains id, title, abstract, authors, publication_date, landing_page_url, pdf_url.
    """
    try:
        works = (
            Works()
            .select(
                "id,title,abstract_inverted_index,authorships,publication_date,primary_location"
            )
            .search(query)
            .sort(relevance_score="desc")
            .get(per_page=1)
        )
    except Exception as e:
        print(f"Error fetching works for query '{query}': {e}")
        return []

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

            results.append({
                "id": work_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "publication_date": publication_date,
                "landing_page_url": landing_page_url,
                "pdf_url": pdf_url
            })
        except Exception as ex:
            print(f"Error processing work '{work.get('id', 'unknown')}': {ex}")
            continue

    return results


def fetch_works_multiple_queries(queries):
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
    - pdf_url: Direct URL to the PDF, if available. Prefer this over landing_page_url where possible

    Parameters:
    - queries (List[str]): List of search keywords or phrases to query in OpenAlex.

    Returns:
    - List[dict]: A single, combined list of work metadata dictionaries from all queries.
    """
    all_results = []
    for query in queries:
        try:
            works = _fetch_works_single_query(query)
            all_results.extend(works)
        except Exception as e:
            print(f"Error fetching works for query '{query}': {e}")
    return all_results


if __name__ == "__main__":
    print(fetch_works_multiple_queries(["biomedical", "LLMs"]))
