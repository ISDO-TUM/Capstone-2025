import llm.Prompts as prompts
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from config.settings import Config
from llm.tools.Tools import get_tools
from langgraph.prebuilt import create_react_agent

from langchain_core.messages import HumanMessage
RECURSION_LIMIT = 2 * 4 + 1
user_message = prompts.user_message
tools = get_tools()
llm = ChatOpenAI(api_key=Config.OPENAI_API_KEY, temperature=0.4, model="gpt-4") #todo import this from llm definition
system_prompt = prompts.system_prompt
agent = create_react_agent(model=llm, tools=tools)


def trigger_agent(user_message : str):
    return agent_executor.invoke({'messages': [system_prompt, HumanMessage(content=user_message)]})

if __name__ == '__main__':
    for step in agent.stream(
    {"messages": [system_prompt, HumanMessage(content=user_message)]},
    {"recursion_limit": RECURSION_LIMIT},
    stream_mode="values",
    ):
        step["messages"][-1].pretty_print()
    #print(trigger_agent(user_message)['messages'][-1])