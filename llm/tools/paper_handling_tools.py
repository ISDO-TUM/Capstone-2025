from __future__ import annotations

import logging
from typing import Any, Dict, List
import json
from llm.LLMDefinition import LLM
from langchain_core.tools import tool

from chroma_db.chroma_vector_db import chroma_db
from utils.status import Status
from llm.Embeddings import embed_papers
from database.papers_database_handler import insert_papers
from paper_handling.paper_handler import fetch_works_multiple_queries
from llm.util.agent_custom_filter import _matches, _OPERATORS

logger = logging.getLogger(__name__)


@tool
def update_papers(queries: list[str]) -> str:
    """
    Tool Name: update_papers
    Description:
        This tool updates the paper database with the latest research papers and their embeddings
        based on a list of search queries. It performs the following steps:
        1. Fetches new papers using the provided list of queries.
        2. Stores the fetched papers in a PostgreSQL database, removing any duplicates.
        3. Computes and stores embeddings for the newly stored papers.
    Use Case:
        Use this tool when you want to refresh the paper database with the latest research and ensure
        that all relevant papers have updated embeddings for ranking or similarity comparison tasks.
    Input:
        queries (list[str]): A list of strings corresponding to the user's interests to search for relevant papers.
        When generating search queries based on the user's interests, make sure to preserve meaningful multi-word expressions as single, coherent search terms. For example, if the user mentions "ice cream," do not split this into "ice" and "cream" — treat it as a unified concept: "ice cream."
        Generate search queries that reflect the actual intent of the user's interest, emphasizing quality over quantity. Avoid breaking compound phrases into individual words unless they are clearly independent concepts.
        Use concise and targeted queries that represent whole ideas, domains, or research topics. Only split input into multiple queries if doing so improves the relevance or diversity of the results without losing semantic meaning.

        Examples:
            - User: "I'm interested in machine learning and neural networks"
            queries: ["machine learning", "neural networks"]

            - User: "I like ice cream and computer vision"
            queries: ["ice cream", "computer vision"]

        Avoid:
            - ["ice", "cream", "computer", "vision"]
    Output:
        A status message string indicating whether the process completed successfully without errors,
        or completed with some errors that can be ignored.
    Returns:
        str: A human-readable summary of the update operation's result.
    """
    try:
        fetched_papers, status_fetch = fetch_works_multiple_queries(queries)

        status_postgres, deduplicated_papers = insert_papers(fetched_papers)
        # todo print how many new papers for debugging

        embedded_papers = []
        for paper in deduplicated_papers:
            embedding = embed_papers(paper['title'],
                                     paper['abstract'])
            embedded_paper = {
                'embedding': embedding,
                'hash': paper['hash'],
            }
            embedded_papers.append(embedded_paper)

        status_chroma = chroma_db.store_embeddings(embedded_papers)

        if all([
            status_fetch == Status.SUCCESS,
            status_postgres == Status.SUCCESS,
            status_chroma == Status.SUCCESS
        ]):
            logger.info("Updating paper database successfully.")
            return ("Paper database has been updated with the latest papers & embeddings. There were no errors. "
                    "Now you can rank the papers.")
        else:
            logger.error("Updating paper database failed.")
            return ("Paper database has been updated with the latest papers & embeddings. There were some errors. "
                    "Ignore the errors and proceed with ranking the papers.")

    except Exception as e:
        logger.error(f"Updating paper database failed: {e}")
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


logger = logging.getLogger(__name__)


@tool
def accept(confirmation: str) -> str:
    """
    Agent has accepted the current results.
    No reformulation or retry is needed.
    """
    return json.dumps({
        "status": "accepted",
        "message": "The current paper results meet the quality requirements. Proceeding..."
    })


@tool
def retry_broaden(keywords: list[str], query_description: str = "") -> str:
    """
    Agent tool to broaden the user's original keyword list using LLM.

    Input:
    {
        "query_description": "AI for rare diseases",
        "keywords": ["rare disease", "machine learning", "diagnosis"]
    }

    Output:
        JSON-formatted string with new keywords, or fallback message.
    """
    if not keywords:
        return json.dumps({
            "status": "error",
            "message": "No keywords provided. Cannot broaden."
        })

    prompt = f"""
    You are an academic research assistant helping users improve their scientific paper search using the OpenAlex API.

    The user has provided:
    - A natural language description of their research goal
    - A small list of initial keywords they used to search for papers

    Your task is to intelligently **broaden and optimize** the keyword list. Follow these rules:

    1. Only suggest **2 to 4** high-quality keywords.
    2. Prioritize **concepts or terms that would likely exist in academic knowledge graphs** (like OpenAlex).
    3. Avoid exact duplicates or overly generic terms (e.g. "research", "science").
    4. Prefer well-known **scientific disciplines**, **methods**, or **subfields** related to the original topic.
    5. Assume the keywords will be used in a query like:
    `filter=keywords.id:keyword1|keyword2|...` which uses AND matching — so do **not** add too many.

    Respond only with a JSON list of new keywords (do not include the original ones), e.g.:
    ["metabolomics", "cellular respiration", "photoperiodism"]

    User research description: "{query_description}"

    Original keywords: {json.dumps(keywords)}

    Broadened keyword list (JSON format only):
    """

    response = LLM.invoke(prompt)

    try:
        broadened_keywords = json.loads(response.content)
        if isinstance(broadened_keywords, list):
            logger.info("Broadened keyword query.")
            return json.dumps({
                "broadened_keywords": broadened_keywords,
                "status": "success"
            })
        else:
            raise ValueError
    except Exception as e:
        logger.error(f"Error while broadening the keyword query: {e}")
        return json.dumps({
            "status": "error",
            "message": "Could not parse broadened keyword list."
        })


@tool
def reformulate_query(keywords: list[str], query_description: str = "") -> str:
    """
    Reformulates the user's query to better capture academic search intent.

    Input:
    {
        "query_description": "ML in healthcare diagnosis",
        "keywords": ["ml", "healthcare", "diagnosis"]
    }

    Output:
        JSON string with reformulated query description and keywords.
    """
    if not query_description:
        logger.error("Query description was missing")
        return json.dumps({
            "status": "error",
            "message": "Missing query description."
        })

    prompt = f"""
    You are an AI-powered academic assistant helping researchers refine their literature search strategy using OpenAlex.

    The user has submitted:
    - A vague or imprecise research topic
    - A list of keywords they initially used in the search

    Your task is to **clarify the research intent** and **optimize the keyword list** so that:
    1. The topic becomes academically precise and focused
    2. The keywords are suitable for high-quality retrieval in OpenAlex

    🔎 Guidelines for Keyword Optimization:
    - Suggest only **2 to 4** highly relevant keywords
    - Prefer keywords that match academic fields, subdisciplines, or research methods
    - Avoid filler words, overly generic terms, or keyword duplication
    - Assume the keywords will be used in a strict **AND** filter (i.e. all must be present), so select carefully to **maximize relevance while maintaining sufficient recall**

    💡 Your goal is **focus**, not breadth. Do not add unrelated or tangential concepts.

    Input:
    - User query description: "{query_description}"
    - Original keywords: {json.dumps(keywords)}

    Respond with a JSON object of the form:
    {{
    "reformulated_description": "More focused and academically clear version of the user's research goal",
    "refined_keywords": ["...", "...", "..."]
    }}
    """

    response = LLM.invoke(prompt)

    try:
        reformulated = json.loads(response.content)
        logger.info("Query reformulated successfully.")
        return json.dumps({
            "status": "success",
            "result": reformulated
        })
    except Exception as e:
        logger.error(f"Error reformulating the query: {e}")
        return json.dumps({
            "status": "error",
            "message": "Could not parse reformulated query."
        })


@tool
def detect_out_of_scope_query(query_description: str) -> str:
    """
    Checks whether a user query is nonsensical or unrelated to scientific research.

    Input:
    {
        "query_description": "How are you?"
    }

    Output:
        JSON object with:
        - status: "valid" or "out_of_scope"
        - reason: explanation if out_of_scope
    """
    if not query_description.strip():
        return json.dumps({
            "status": "out_of_scope",
            "reason": "Query is empty or whitespace."
        })

    prompt = f"""
    You are a research paper search assistant.

    Analyze the following user query and determine if it is a valid academic topic
    for a scientific literature search or if it is out-of-scope (e.g., a greeting,
    joke, personal opinion, or unrelated to science).

    Query: "{query_description}"

    Respond with a JSON object like:
    {{
        "status": "valid" | "out_of_scope",
        "reason": "..."  // explanation for decision
    }}
    """

    response = LLM.invoke(prompt)

    try:
        logger.info("Checking if query is out of scope.")
        return json.dumps(json.loads(response.content))
    except Exception as e:
        logger.error(f"Failed to parse response: {e}")
        return json.dumps({
            "status": "error",
            "reason": "Failed to parse response. Raw content: " + response.content
        })


@tool
def narrow_query(query_description: str, keywords: list[str]) -> str:
    """
    Agent tool that takes a broad set of keywords and returns a *narrower / more specific*
    keyword list that stays fully inside the user’s topic.

    Parameters
    ----------
    query_description : str
        The user prompt string written in natural language
    keywords : list[str]
        Current (possibly too generic) keyword list.

    Returns
    -------
    str
        JSON string:
        {
            "status": "success" | "error",
            "narrowed_keywords": [...],   # only if success
            "message": "..."              # optional info / error reason
        }
    """

    if not keywords:
        return json.dumps({
            "status": "error",
            "message": "No keywords provided. Cannot narrow."
        })

    prompt = f"""
    You are an academic research assistant.

    The user’s current keyword list is *too broad*.
    Your job is to **narrow / focus** the query so it retrieves _fewer, more precise_
    papers from OpenAlex.

    – Keep the core topic absolutely intact.
    – Drop purely generic filler terms (e.g. "science", stand-alone "analysis")
  **unless the term is clearly domain-defining** (e.g. “Data Science”,
  “spectral analysis”, “metabolite analysis”).
    – Prefer specific subfields, methods, data types, time periods, organisms, etc.
    – Do **NOT** add unrelated adjacent ideas.
    – Remove duplicates.
    – Limit the result to **5–8** focused keywords.

    Output **only** a valid JSON list – no commentary.

    User query description:
    \"\"\"{query_description}\"\"\"

    Original keywords:
    {json.dumps(keywords)}

    Return the narrowed keyword list (JSON only):
    """

    response = LLM.invoke(prompt)

    try:
        narrowed = json.loads(response.content)
        if not isinstance(narrowed, list):
            raise ValueError("Result must be a JSON list")
        logger.info("Narrowed keyword list generated.")

        # If the narrowed list is empty or too similar to the original, return a failure status
        # and the original keywords
        if not narrowed:
            return json.dumps({
                "status": "failed",
                "narrowed_keywords": keywords
            })

        return json.dumps({
            "status": "success",
            "narrowed_keywords": narrowed
        })
    except Exception as e:
        logger.error(f"Narrow query parsing failed: {e}")
        return json.dumps({
            "status": "error",
            "message": "Could not parse narrowed keyword list."
        })


@tool
def multi_step_reasoning(query_description: str,
                         max_subqueries: int = 3,
                         max_keywords: int = 5) -> str:
    """
    Break a LONG / multi-topic research query into focused sub-queries.

    Input  (passed as kwargs!) :
      query_description : str   – the raw user prompt
      max_subqueries    : int   – upper-bound on splits (default 3)
      max_keywords      : int   – keyword cap per split     (default 5)

    Output: JSON string
    {
      "status": "success",
      "subqueries": [
        {
          "sub_description": "...",
          "keywords": ["k1","k2", ... up to max_keywords]
        },
        ...
      ],
      "reasoning": "short explanation"
    }
    """

    prompt = f"""
    You are an expert academic search planner.

    The user’s query is potentially too broad to retrieve precise
    papers in a single OpenAlex search (keyword limit ≈ {max_keywords}).

    The users query is: {query_description}

    • Decompose it into up to {max_subqueries} coherent sub-topics.
      – Each sub-topic should be **independent** and “searchable”.
      – Preserve the scientific intent; do not invent new themes.
    • For EACH sub-topic produce a keyword list
      (≤ {max_keywords} items, no duplicates, no stop-words).

    Return ONLY valid JSON with this exact layout:
    {{
      "status": "success",
      "subqueries": [
        {{"sub_description": "...", "keywords": ["...", ...] }},
        ...
      ],
      "reasoning": "why the split helps"
    }}
    """

    try:
        response = LLM.invoke(prompt)
        plan_obj = json.loads(response.content)

        # explicit validation (no assert)
        if plan_obj.get("status") != "success":
            raise ValueError("Planner did not return status=success")

        if not isinstance(plan_obj.get("subqueries"), list) or not plan_obj["subqueries"]:
            raise ValueError("Planner returned an empty or invalid subqueries list")

        logger.info("Multi-step reasoning plan generated.")
        return json.dumps(plan_obj)

    except Exception as e:
        logger.error("Query-split failed: %s", e)
        return json.dumps({
            "status": "error",
            "message": "Could not parse sub-query list"
        })


def apply_filter_spec_to_papers(
    papers: List[Dict[str, Any]],
    filter_spec: Dict[str, Dict[str, Any]]
) -> dict:
    """
    Applies a filter_spec to a list of papers and returns the filtered results.
    """
    allowed_fields = {
        "authors", "publication_date", "fwci",
        "citation_normalized_percentile", "cited_by_count",
        "counts_by_year", "similarity_score",
    }
    for filter_field, rule in filter_spec.items():
        if filter_field not in allowed_fields:
            return {
                "status": "error",
                "message": f"Unknown metric '{filter_field}' in filter_spec"
            }
        if rule["op"] not in _OPERATORS:
            return {
                "status": "error",
                "message": f"Unsupported operator '{rule['op']}'"
            }

    kept_papers: list[dict] = []
    for paper in papers:
        try:
            if all(_matches(paper.get(metric), rule["op"], rule["value"])
                   for metric, rule in filter_spec.items()):
                kept_papers.append(paper)
        except Exception as exc:
            logger.debug("Skip paper due to comparison error: %s", exc)

    return {
        "status": "success",
        "filters": filter_spec,
        "kept_count": len(kept_papers),
        "kept_papers": kept_papers,
        "reasoning": f"Applied {len(filter_spec)} metric filter(s)"
    }


@tool
def filter_papers_by_nl_criteria(
    papers: List[Dict[str, Any]],
    criteria_nl: str
) -> str:
    """
    Filter a list of OpenAlex paper dicts using a natural language criteria string.

    The tool will:
    1. Convert the NL criteria to a structured filter_spec using LLM.
    2. Apply the filter_spec to the papers.
    3. Return the filtered papers and applied filters.

    Args:
        papers: List of paper dicts.
        criteria_nl: Natural language filter description.

    Returns:
        JSON string with status, applied filters, kept_count, kept_papers, and reasoning.
    """
    PARSE_PROMPT = f"""
    You are a filtering assistant.

    Translate the user's request into a JSON **object** using ONLY the metric
    names below **exactly as written**.  Do not invent new fields.

    Allowed metric names:
    • authors
    • publication_date
    • fwci
    • citation_normalized_percentile
    • cited_by_count
    • counts_by_year
    • similarity_score

    Allowed operators: ">", ">=", "<", "<=", "==", "!=", "in", "not in"

    Schema per entry:
    "<metric>": {{"op": "<operator>", "value": <number|string|list>}}

    Examples
    --------
    NL:  Keep papers after 2022 with similarity above 0.8
    JSON:
    {{
    "publication_date": {{"op": ">", "value": 2022}},
    "similarity_score": {{"op": ">", "value": 0.8}}
    }}

    NL:  Only papers with >25 citations from Nature
    JSON:
    {{
    "cited_by_count": {{"op": ">", "value": 25}},
    "authors":        {{"op": "in", "value": ["Nature"]}}
    }}

    Return the JSON only – no markdown.
    Request:
    \"\"\"{criteria_nl}\"\"\"
    """
    try:
        llm_out = LLM.invoke(PARSE_PROMPT).content.strip()
        filter_spec = json.loads(llm_out)
        logger.info("LLM-generated filter_spec: %s", filter_spec)
    except Exception as e:
        logger.error("Failed to obtain filter_spec from NL: %s", e)
        return json.dumps(
            {"status": "error",
             "message": "Could not parse criteria_nl into a filter spec"}
        )

    result = apply_filter_spec_to_papers(papers, filter_spec)
    return json.dumps(result)


def main():
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import HumanMessage
    from llm.tools.Tools_aggregator import get_tools
    from llm.LLMDefinition import LLM
    from llm.util.agent_log_formatter import format_log_message

    print("\n========== PHASE 1: DIRECT TOOL TESTING ==========\n")

    tool_inputs = {
        "retry_broaden": [
            {"query_description": "My research is about yeast metabolism under moonlight.", "keywords": ["yeast", "metabolism", "moonlight"]},
            {"query_description": "Low citation results on a very specific variant of quantum Hall effects.", "keywords": ["quantum hall", "edge states", "low temperature"]},
            {"query_description": "I only got one result for 'subtypes of algae in Norwegian fjords' — can you expand that?", "keywords": ["algae", "Norwegian fjords", "taxonomy"]}
        ],
        "reformulate_query": [
            {"query_description": "biotech bio something cancer cell therapy general stuff", "keywords": ["biotech", "cancer", "cell therapy"]},
            {"query_description": "fuzzy logic relevance matching NLP graphs paper recommendation system vague idea", "keywords": ["fuzzy logic", "NLP", "recommendation"]}
        ],
        "accept": [
            {"confirmation": "yes"},
            {"confirmation": "yes"}
        ],
        "detect_out_of_scope_query": [
            {"query_description": "How are you doing today?"}
        ]
    }

    for tool_name, input_list in tool_inputs.items():
        print(f"\n🛠️ Tool: {tool_name.upper()}")
        for inputs in input_list:
            print(f"Input: {inputs}")
            if tool_name == "retry_broaden":
                output = retry_broaden.invoke(inputs)
            elif tool_name == "reformulate_query":
                output = reformulate_query.invoke(inputs)
            elif tool_name == "accept":
                output = accept.invoke(inputs)
            elif tool_name == "detect_out_of_scope_query":
                output = detect_out_of_scope_query.invoke(inputs)
            else:
                output = "❌ Unknown tool"
            print("Output:", output)
            print("-" * 60)

    print("\n========== PHASE 2: AGENT STREAMING TESTING ==========\n")

    tools = get_tools()
    agent = create_react_agent(model=LLM, tools=tools)

    system_prompt = HumanMessage(content="""
    You are a helpful academic research assistant.
    You have access to tools like `retry_broaden`, `reformulate_query`, `accept`, and `detect_out_of_scope_query`.

    Based on the user query, you must decide whether to:
    - Broaden overly specific queries
    - Reformulate vague or poorly phrased ones
    - Accept a valid query if it needs no changes
    - Detect and reject queries that are not related to scientific research

    Your final output must always return the tool result only. Think carefully and choose the right action.
    """)

    # Combine all textual query inputs for testing the agent
    agent_test_queries = [
        "My research is about yeast metabolism under moonlight.",
        "Low citation results on a very specific variant of quantum Hall effects.",
        "I only got one result for 'subtypes of algae in Norwegian fjords' — can you expand that?",
        "biotech bio something cancer cell therapy general stuff",
        "fuzzy logic relevance matching NLP graphs paper recommendation system vague idea",
        "Applications of transformers in biomedical entity recognition",
        "Recent developments in reinforcement learning for robotics control",
        "How are you doing today?"
    ]

    def stream_agent_reasoning(agent, query: str):
        print(f"\n🔍 Query: {query}\n")
        last_step = None
        for step in agent.stream(
            {"messages": [system_prompt, HumanMessage(content=query)]},
            {"recursion_limit": 6},
            stream_mode="values",
        ):
            log = step["messages"][-1].pretty_repr()
            print(format_log_message(log))
            last_step = step

        if last_step:
            print("\n✅ Final Agent Output:\n", last_step["messages"][-1].content)
        else:
            print("\n⚠️ Agent produced no output.\n")

    for query in agent_test_queries:
        stream_agent_reasoning(agent, query)


if __name__ == "__main__":
    main()
