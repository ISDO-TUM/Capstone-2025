import json
from langchain_core.tools import tool


@tool
def select_relevant_titles(input: str) -> str:
    """
    Input str should be a JSON string with:
      - 'papers': a list of paper titles and links dict
      - 'query': the user query or research interest

    Example:
    {
      "papers": [
        {
            "title":"Deep Learning in Medicine",
            "link": "example link"
        },
        {
            "title" : "Climate Change Models",
            "link": "example link"
        },
        {
            "title": "Transformer Architectures",
            "link": "example link"
        }],
      "query": "machine learning for healthcare"
    }

    Returns a comma-separated string of titles and links most relevant to the query.
    """

    try:
        data = json.loads(input)
        papers = data.get("papers", [])
        query = data.get("query", "")

        if not papers or not query:
            return "Missing 'papers' or 'query' in input."

        return f"Filter these papers: {papers} based on this query: '{query}', select the 5-10 most relevant ones"

    except Exception as e:
        return f"Error parsing input: {e}"
