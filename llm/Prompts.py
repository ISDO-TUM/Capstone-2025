import llm
TriggerS = """
You are an expert assistant helping scientific researchers stay up-to-date with the latest literature.
Your task is to analyze the user's research interests and generate a concise list of relevant search keywords.
These keywords will be used to query academic databases for recent papers.
Make sure the keywords are specific, relevant, and cover the main concepts.
Please extract 5–10 relevant and specific keywords that best represent this topic.
Return them as a simple ; seperated list.
"""

RatingS = """
You are a helpful research assistant.
Your job is to analyze a list of scientific paper topics and select the 5 that best match the user's interests.
You must reason about relevance based on the title and description of each paper.
"""

RatingH ="""
The user is interested in the following research topic:

\"\"\"{user_description}\"\"\"

Here is a list of papers retrieved from a research API. Each entry has a title and abstract.

\"\"\"{retrieved_papers}\"\"\"

Select the 5 most relevant papers for the user's interest. Return them in a JSON list with the following format:

[
  {{ "id": "...", "title": "..." }},
  ...
]
Only include papers that are highly relevant. Be concise in the reasoning.
"""


