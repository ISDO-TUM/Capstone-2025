from typing import Any
import json
from llm.LLMDefinition import LLM 
import llm.Prompts as prompts

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


def check_relevance_threshold(papers_with_relevance_scores: list[dict], threshold: float, min_papers: int = 3) -> bool:
    """
    Checks if the similarity scores in the list of papers meet the specified threshold.
    Only considers the top N papers (default 3) and requires at least that many to proceed.

    Args:
        papers_with_relevance_scores: List of paper dictionaries including 'similarity_score'.
        threshold: Minimum similarity score to consider a paper relevant.
        min_papers: Minimum number of papers required to evaluate satisfaction.

    Returns:
        True if the top N papers meet the threshold; otherwise False.
    """
    if len(papers_with_relevance_scores) < min_papers:
        return False

    top_papers = papers_with_relevance_scores[:min_papers]
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

    Respond with a JSON object with the following structure:
    {{
    "action": "...",  // one of: accept, retry_broaden, reformulate_query
    "reason": "..."   // brief explanation why the action was chosen (max 2 sentences)
    }}
    Only output the JSON object. Do not include any other text or formatting.

    Guidance for choosing:
    - Choose "accept" if the majority of papers are relevant, well-cited, and recent.
    - Choose "retry_broaden" if the results are too narrow or too few.
    - Choose "reformulate_query" if the query seems to miss the intent or is too vague or off-topic.

    Now decide based on the following paper metadata:

    {formatted_metadata}

    Respond with a JSON object with the following structure:
    {{
    "action": "...",  // one of: accept, retry_broaden, reformulate_query
    "reason": "..."   // brief explanation why the action was chosen (max 2 sentences)
    }}
    Only output the JSON object. Do not include any other text or formatting.
    """
    llm = LLM
    response = llm.invoke(prompt)

    try:
        parsed = json.loads(response.content)
        action = parsed["action"]
        reason = parsed["reason"]
    except json.JSONDecodeError:
        print(response.content.strip().lower())
        raise ValueError("Agent response could not be parsed. Check format and content.")

    return action, reason

    #return response.content.strip().lower()



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
    

def quality_control_loop(retrieved_papers: list[dict], current_query: str, attempt: int = 0):
    """
    Wraps steps 5–7 together.
    - Calls `check_relevance_threshold`
    - If False, calls `decide_next_action`
    - Then `retry_with_modified_parameters` and loops if necessary
    """
    threshold = 0.7  # Example threshold for relevance
    is_satisfactory = check_relevance_threshold(retrieved_papers, threshold, min_papers=3)

    if is_satisfactory:
        print(f"Attempt {attempt}: Papers are satisfactory (accepted by similarity score, no agent action).")
        return None

    print(f"Number of retrieved papers: {len(retrieved_papers)}")
    action, reason = decide_next_action(retrieved_papers, current_query)
    print(f"Attempt {attempt}: Decided action - {action}")
    print(f"Reason for action: {reason}")

    # In the future add methods so the agent can modify the query based on the action (either broaden, or reformulate)

    # After query is reformulated or broadened, we want to fetch new papers
    new_retrieved_papers = []
    # new_retrieved_papers = get_paper_basic_data([next_query])

    return None


if __name__ == "__main__":

    papers_with_metadata = json.loads
    ("""
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
        },
        {
        "id": "https://openalex.org/W1234567890",
        "title": "Optimizing Clinical Workflow Integration of LLM-Based Decision Support Systems",
        "abstract": "Recent advances in large language models (LLMs) have opened new frontiers for decision support in clinical environments. This paper presents a framework for aligning LLM capabilities with routine physician tasks by incorporating real-time feedback, structured knowledge grounding, and task-specific fine-tuning. We evaluate our approach on a multi-specialty dataset containing 75,000 structured clinical interactions and introduce MedAlignBench, a benchmark suite simulating realistic use cases across diagnostics, prescription drafting, and medical documentation. Results show significant improvements in clinician satisfaction and response accuracy, especially when models are tailored to workflow-specific prompts.",
        "authors": "Alicia Zhang, David Patel, Rana Al-Hassan, Thomas L. Lee",
        "publication_date": "2025-05-18",
        "fwci": 1.42,
        "citation_normalized_percentile": 82.3,
        "cited_by_count": 12,
        "counts_by_year": [{"year": 2025, "count": 12}],
        "similarity_score": 0.79,
        "topics": [
            {
                "topic": "Scientific Computing and Data Management",
                "score": 0.89,
                "subfields": ["Healthcare Informatics"],
                "fields": ["Decision Sciences"],
                "domains": ["Social Sciences"]
            },
            {
                "topic": "Large Language Models in Healthcare",
                "score": 0.85,
                "subfields": ["Medical AI"],
                "fields": ["Computer Science"],
                "domains": ["Health Sciences"]
            }
        ],
        "landing_page_url": "https://doi.org/10.1234/medalign.2025.005",
        "pdf_url": "https://arxiv.org/pdf/medalign.2025.005.pdf"
        }
        ]
    """)

    print("\n========== Test Case 1: Query with precomputed similarity scores ==========")
    quality_control_loop(papers_with_metadata, prompts.user_message)

    print("\n========== Test Case 2: No similarity scores (should invoke agent) ==========")
    query_two_papers = fetch_works_multiple_queries(queries=[prompts.user_message_two_keywords])
    quality_control_loop(query_two_papers, prompts.user_message_two)

    print("\n========== Test Case 3: No similarity scores (should invoke agent) ==========")
    query_three_papers = fetch_works_multiple_queries(queries=[prompts.user_message_three_keywords])
    quality_control_loop(query_three_papers, prompts.user_message_three)

    print("\n========== Test Case 4: No similarity scores (should invoke agent) ==========")
    query_four_papers = fetch_works_multiple_queries(queries=[prompts.user_message_four_keywords])
    quality_control_loop(query_four_papers, prompts.user_message_four)

    print("\n========== Test Case 5: Defective query – agent should suggest reformulation ==========")
    query_five_papers = fetch_works_multiple_queries(queries=[prompts.user_message_five_keywords])
    quality_control_loop(query_five_papers, prompts.user_message_five)

    print("\n========== Test Case 6: Overly narrow query – agent should suggest broadening ==========")
    query_six_papers = fetch_works_multiple_queries(queries=[prompts.user_message_six_keywords])
    quality_control_loop(query_six_papers, prompts.user_message_six)

    print("\n========== Test Case 8: Non-sensical query – agent should trigger correction ==========")
    query_eight_papers = fetch_works_multiple_queries(queries=["Hello"])
    quality_control_loop(query_eight_papers, "Hello")