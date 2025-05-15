import json
from langchain_core.tools import tool

#@tool
def select_relevant_titles(input: str) -> str:
    """
    Input str should be a JSON string with:
      - 'titles': a list of paper titles
      - 'query': the user query or research interest

    Example:
    {
      "titles": ["Deep Learning in Medicine", "Climate Change Models", "Transformer Architectures"],
      "query": "machine learning for healthcare"
    }

    Returns a comma-separated string of titles most relevant to the query.
    """
   
    try:
        data = json.loads(input)
        titles = data.get("titles", [])
        query = data.get("query", "")

        if not titles or not query:
            return "Missing 'titles' or 'query' in input."

        return f"Filter these titles: {titles} based on this query: '{query}', select the 5-10 most relevant ones"

    except Exception as e:
        return f"Error parsing input: {e}"