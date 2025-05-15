import llm.Prompts as prompts
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from config.settings import Config
from llm.tools.Tools import get_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

user_message = prompts.user_message

llm = ChatOpenAI(api_key=Config.OPENAI_API_KEY, temperature=0.4, model="gpt-4") #todo import this from llm definition
system_prompt = prompts.system_prompt
agent_executor = create_react_agent(model=llm, tools=get_tools())

def trigger_agent(user_message : str):
    return agent_executor.invoke({'messages': [system_prompt, HumanMessage(content=user_message)]})

if __name__ == '__main__':
    for step in agent_executor.stream(
    {"messages": [system_prompt, HumanMessage(content=user_message)]},
    stream_mode="values",
    ):
        step["messages"][-1].pretty_print()
    #print(trigger_agent(user_message)['messages'][-1])