import llm
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.messages import HumanMessage

user_message = """
I'm researching the application of Gaussian Process Bandits in optimizing machine learning tasks. Specifically, I'm interested in enhancing exploration-exploitation trade-offs and improving computational efficiency through GPU acceleration for large-scale experiments.
"""

system_prompt = SystemMessage(content = """
  You are an expert assistant helping scientific researchers stay up-to-date with the latest literature.
  Your task is to analyze the user's research interests and use your available tools to query papers titles 
  and then select the most relevant ones. You have a variety of tools that let you query papers in relation to the user interests and to organize them to rank them.
  Do not make up paper names that are not returned by tool calls. In that case say that you could not find any papers.
  """)
   