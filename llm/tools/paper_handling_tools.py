from typing import Any
import json
from llm.LLMDefinition import LLM 
from llm.Prompts import user_message

from paper_handling.paper_handler import fetch_works_multiple_queries


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


def check_relevance_threshold(papers_with_relevance_scores: list[dict], threshold: float) -> bool:
    """
    Step 5: Checks if the similarity scores in the list of papers meet the specified threshold.
    Returns True if results are satisfactory, False otherwise.

    Args:
        papers_with_relevance_scores: A list of dictionaries where each dict represents a paper and includes a 'similarity_score' key.
        threshold: The minimum similarity score required for a paper to be considered relevant.

    Returns:
        True if all relevant papers meet the threshold (uses top 3 if available), otherwise False.
    """
    top_papers = papers_with_relevance_scores[:3] if len(papers_with_relevance_scores) > 3 else papers_with_relevance_scores
    return all(paper.get("similarity_score", 0.0) >= threshold for paper in top_papers)


def decide_next_action(papers_with_metadata: list[dict], user_query: str) -> str:
    """
    Step 6: Agent logic to decide what to do next if results are not satisfactory.
    Returns one of: "retry_broaden", "reformulate_query", "lower_threshold", or "accept".
    """

    formatted_metadata = "\n\n".join(
    f"""Paper {i+1}:
        - Title: {paper.get("title", "N/A")}
        - Similarity Score: {paper.get("similarity_score", "N/A")}
        - Citation Count: {paper.get("cited_by_count", "N/A")}
        - FWCI: {paper.get("fwci", "N/A")}
        - Citation Percentile: {paper.get("citation_normalized_percentile", "N/A")}
        - Publication Date: {paper.get("publication_date", "N/A")}
        - Abstract: {paper.get("abstract", "N/A")}
        - Topics: {", ".join(t.get("topic", "N/A") for t in paper.get("topics", []))}
        - Subfields: {", ".join(sf for t in paper.get("topics", []) for sf in t.get("subfields", []))}
        - Fields: {", ".join(f for t in paper.get("topics", []) for f in t.get("fields", []))}
        - Domains: {", ".join(d for t in paper.get("topics", []) for d in t.get("domains", []))}
    """
    for i, paper in enumerate(papers_with_metadata)
    )

    prompt = f"""
    You are an intelligent research assistant responsible for evaluating a set of research papers returned from a query.

    This is the user initial query: "{user_query}"

    For each paper, you have access to metadata such as:
    - similarity score (relevance to the original query),
    - citation count,
    - field-weighted citation impact (FWCI),
    - title,
    - abstract.

    Your goal is to assess whether the current set of results is satisfactory, or whether another action should be taken.

    Please choose **one** of the following actions based on the quality and relevance of the papers:
    - "accept": The papers are relevant and high-quality.
    - "retry_broaden": The papers are too narrow or too few, try a broader version of the current query.
    - "reformulate_query": The current query is off, and should be reformulated to better capture the user intent.
    - "lower_threshold": The threshold for similarity or quality might be too high, and lowering it could yield more useful results.

    You may consider papers satisfactory if:
    - Most have high similarity scores (e.g. > 0.7),
    - They include recent and well-cited research,
    - They align well with the query topic as indicated by abstract and title.

    Now decide based on the following paper metadata:

    {formatted_metadata}
    """
    llm = LLM
    response = llm.invoke(prompt)
    return response.content.strip().lower()



def retry_with_modified_parameters(action: str, current_query: str, attempt: int) -> str:
    """
    Step 7: Based on the agent’s decision, generates the next query or parameters.
    References the output of `decide_next_action`.
    """

    if action == "accept":
        print(f"Action: {action} on attempt {attempt}. Found papers satisfactory.")
        # return current_query  # No change needed, accept the current query

    elif action == "retry_broaden":
        print(f"Action: {action} on attempt {attempt}. Retrying with a broader query.")
        # Broaden the query by adding more general terms or synonyms
        # broadened_query = f"{current_query} broadening search terms"
        # return broadened_query

    elif action == "reformulate_query":
        print(f"Action: {action} on attempt {attempt}. Reformulating the query.")
        # Reformulate the query to better capture user intent
        # reformulated_query = f"Reformulated: {current_query} with better keywords"
        # return reformulated_query

    else:
        raise ValueError(f"Unknown action: {action}")
    

def quality_control_loop(retrieved_papers: list[dict], current_query: str, attempt: int = 0) -> list[dict]:
    """
    Wraps steps 5–7 together.
    - Calls `check_relevance_threshold`
    - If False, calls `decide_next_action`
    - Then `retry_with_modified_parameters` and loops if necessary
    """
    threshold = 0.7  # Example threshold for relevance
    is_satisfactory = check_relevance_threshold(retrieved_papers, threshold)

    if is_satisfactory:
        print(f"Attempt {attempt}: Papers are satisfactory.")
        return retrieved_papers 

    action = decide_next_action(retrieved_papers, current_query)
    print(f"Attempt {attempt}: Decided action - {action}")

    next_query = retry_with_modified_parameters(action, current_query, attempt)
    
    if next_query == current_query:  # If no change needed, return the papers
        return retrieved_papers

    # TODO: REFETCH PAPERS WITH THE NEW QUERY
    new_retrieved_papers = []
    # new_retrieved_papers = get_paper_basic_data([next_query])  # Simulate fetching with the new query

    return quality_control_loop(new_retrieved_papers, next_query, attempt + 1)


if __name__ == "__main__":

    papers_with_metadata = json.loads("""
    [
        {
        "id": "https://openalex.org/W4410932904",
        "title": "Promising biomedical applications using superparamagnetic nanoparticles",
        "abstract": "No abstract available",
        "authors": "Yosri A. Fahim, Ibrahim W. Hasani, Waleed Mahmoud Ragab",
        "publication_date": "2025-06-02",
        "fwci": null,
        "citation_normalized_percentile": null,
        "cited_by_count": 0,
        "counts_by_year": [],
        "similarity_score": 0.72, 
        "topics": [
        {
            "topic": "Nanoparticle-Based Drug Delivery",
            "score": 1.0,
            "subfields": ["Biomaterials"],
            "fields": ["Materials Science"],
            "domains": ["Physical Sciences"]
        },
        {
            "topic": "Characterization and Applications of Magnetic Nanoparticles",
            "score": 0.9999,
            "subfields": ["Biomedical Engineering"],
            "fields": ["Engineering"],
            "domains": ["Physical Sciences"]
        },
        {
            "topic": "Gold and Silver Nanoparticles Synthesis and Applications",
            "score": 0.9973,
            "subfields": ["Electronic, Optical and Magnetic Materials"],
            "fields": ["Materials Science"],
            "domains": ["Physical Sciences"]
        }
        ],
        "landing_page_url": "https://doi.org/10.1186/s40001-025-02696-z",
        "pdf_url": null
    },
    {
        "id": "https://openalex.org/W4410933080",
        "title": "Enabling Doctor-Centric Medical AI with LLMs through Workflow-Aligned Tasks and Benchmarks",
        "abstract": "<title>Abstract</title> The rise of large language models (LLMs) has profoundly influenced health-care by offering medical advice, diagnostic suggestions, and more. However, their deployment directly toward patients poses substantial risks, as limited domain knowledge may result in misleading or erroneous outputs. To address this challenge , we propose repositioning LLMs as clinical assistants that collaborate with experienced physicians rather than interacting with patients directly. We begin with a two-stage inspiration–feedback survey to identify real-world needs in clinical workflows. Guided by this, we construct DoctorFLAN, a large-scale Chi-nese medical dataset comprising 92,000 Q&A instances across 22 clinical tasks and 27 specialties. To evaluate model performance in doctor-facing applications, 1 we introduce DoctorFLAN-test (550 single-turn Q&A items) and DotaBench (74 multi-turn conversations mimicking realistic scenarios). Experimental results with over ten popular LLMs demonstrate that DoctorFLAN notably improves the performance of open-source LLMs in medical contexts, facilitating their alignment with physician workflows and complementing existing patient-oriented models. This work contributes a valuable resource and framework for advancing doctor-centered medical LLM development.",
        "authors": "Wenya Xie, Qingying Xiao, Yu‐Jun Zheng, Xidong Wang, Junying Chen, Ke Ji, Anningzhe Gao, Prayag Tiwari, Xiang Wan, Feng Jiang, Benyou Wang",
        "publication_date": "2025-06-02",
        "fwci": null,
        "citation_normalized_percentile": null,
        "cited_by_count": 0,
        "counts_by_year": [],
        "similarity_score": 0.87,
        "topics": [
        {
            "topic": "Scientific Computing and Data Management",
            "score": 0.9139,
            "subfields": ["Information Systems and Management"],
            "fields": ["Decision Sciences"],
            "domains": ["Social Sciences"]
        }
        ],
        "landing_page_url": "https://doi.org/10.21203/rs.3.rs-6763537/v1",
        "pdf_url": null
        }
    ]
    """
    )

    action = decide_next_action(papers_with_metadata, user_message)
    print("Agent decision:", action)