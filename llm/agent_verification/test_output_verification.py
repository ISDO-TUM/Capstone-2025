import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from paper_handling.paper_metadata_retriever import get_multiple_topic_works, get_mulitple_topic_works_titles
from TitleVerificationError import verify_agent_titles, TitleVerificationError
from llm.Agent import user_description
from llm.Prompting import llm_call
from llm.Prompts import TriggerS, RatingS, RatingH

print("Script is running...\n")

# Get keywords from the user description
keywords_output = llm_call(TriggerS, user_description)
if keywords_output == -1:
    raise RuntimeError("Failed to retrieve keywords from LLM.")

topic_keywords = [k.strip() for k in keywords_output.split(";") if k.strip()]
print("Keywords from LLM:", topic_keywords)

# Get paper titles from OpenAlex using the keywords
works = get_multiple_topic_works(topic_keywords)
api_titles = get_mulitple_topic_works_titles(works)
api_output_str = "\n".join(api_titles)

print("\n Retrieved titles from API:")
for title in api_titles:
    print(" -", title)

# Ask the LLM to select the most relevant papers
human_message = RatingH.format(
    user_description=user_description,
    retrieved_papers=api_titles
)
agent_response = llm_call(RatingS, human_message)

print("\n Agent response:")
print(agent_response)

# Parse LLM response (JSON)
try:
    parsed = json.loads(agent_response)
    agent_titles = [p["title"] for p in parsed if "title" in p]
except Exception as e:
    print("Failed to parse LLM output as JSON:", e)
    agent_titles = []

# Run verification
print("\n Verifying agent output...\n")
try:
    verified = verify_agent_titles(api_output_str, agent_titles)
    print("Verification successful. Titles matched:")
    for title in verified:
        print(f" - {title}")
except TitleVerificationError as exc:
    print("Verification failed:")
    print(exc)