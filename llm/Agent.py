import llm.Prompts as prompts
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from config.settings import Config
from llm.tools.Tools import get_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage


user_description = """
I'm researching the application of transformer-based language models in biomedical text mining. 
Specifically, I'm interested in methods for extracting relationships between genes, diseases, and drugs from scientific publications, 
as well as improvements in named entity recognition and domain-specific fine-tuning strategies in the biomedical domain.
"""

llm = ChatOpenAI(api_key=Config.OPENAI_API_KEY, temperature=0.4, model="gpt-4") #todo import this from llm definition
system_prompt = prompts.system_prompt
agent_executor = create_react_agent(model=llm, tools=get_tools())

if __name__ == '__main__':
    for step in agent_executor.stream(
    {"messages": [system_prompt, HumanMessage(content=user_description)]},
    stream_mode="values",
    ):
        step["messages"][-1].pretty_print()