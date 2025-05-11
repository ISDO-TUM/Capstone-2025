import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from paper_handling.paper_metadata_retriever import get_works
from TitleVerificationError import verify_agent_titles, TitleVerificationError
from llm.LLMDefinition import LLM
from langchain_core.messages import HumanMessage
from llm import Prompting


# 1. Get real paper titles from OpenAlex
query = "generative models"
works = get_works(query, count=5)
real_titles = [work["title"] for work in works if "title" in work]
api_output_str = "\n".join(real_titles)

print(" Retrieved titles from API:")
for title in real_titles:
    print(" -", title)

# 2. Ask the agent for papers using the Prompting logic
system_msg = "You are a helpful assistant for researchers." #Needs to be updated 
human_msg = "Please list 5 recent papers about generative models"

# Example hardcoded agent output for now
agent_output_str = "\n".join([
    real_titles[0],
    real_titles[2],
    "Agriculture in Central America" #hallucination
])

#use the one below when prompting.py is done.
#agent_output_str = Prompting.multimodal_call(system_msg, human_msg) 
print("\n Agent response:")
print(agent_output_str)

# Split agent output into individual titles
agent_titles_list = agent_output_str.splitlines()

# Run verification
print("\n Verifying agent output...\n")
try:
    verified = verify_agent_titles(api_output_str, agent_titles_list)
    print("Verification successful, titles matched:")
    for title in verified:
        print(f" - {title}")
except TitleVerificationError as exc:
    print("Verification failed:")
    print(exc)