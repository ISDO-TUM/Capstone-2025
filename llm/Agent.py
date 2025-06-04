import llm.Prompts as prompts
from llm.tools.Tools_aggregator import get_tools
from langgraph.prebuilt import create_react_agent
from llm.LLMDefinition import LLM
from langchain_core.messages import HumanMessage

RECURSION_LIMIT = 2 * 4 + 1
user_message = prompts.user_message
tools = get_tools()
llm = LLM
system_prompt = prompts.system_prompt
agent = create_react_agent(model=llm, tools=tools)


def trigger_agent(user_message: str):
    return agent.invoke({'messages': [system_prompt, HumanMessage(content=user_message)]})

def trigger_agent_show_thoughts(user_message: str):
    messages = {}

    for step in agent.stream(
        {"messages": [system_prompt, HumanMessage(content=user_message)]},
        {"recursion_limit": RECURSION_LIMIT},
        stream_mode="values",
    ):
        step["messages"][-1].pretty_print()
        messages = step
    return messages


# Left here to test the agent alone
if __name__ == '__main__':
    # for step in agent.stream(
    #     {"messages": [system_prompt, HumanMessage(content=user_message)]},
    #     {"recursion_limit": RECURSION_LIMIT},
    #     stream_mode="values",
    # ):
    #     step["messages"][-1].pretty_print()
    print(trigger_agent(user_message)['messages'][-1].content)
