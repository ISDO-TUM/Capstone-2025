import llm.Prompts as prompts
from llm.tools.Tools_aggregator import get_tools
from langgraph.prebuilt import create_react_agent
from llm.LLMDefinition import LLM
from langchain_core.messages import HumanMessage

from llm.util.agent_log_formatter import format_log_message

RECURSION_LIMIT = 15
user_message = prompts.user_message
tools = get_tools()
llm = LLM
system_prompt = prompts.system_prompt
agent = create_react_agent(model=llm, tools=tools)


def trigger_agent(user_message: str):
    return agent.invoke({'messages': [system_prompt, HumanMessage(content=user_message)]})


def trigger_agent_show_thoughts(user_message: str):
    """
    A generator that yields each step of the agent's thought process.
    """
    last_step = None

    for step in agent.stream(
            {"messages": [system_prompt, HumanMessage(content=user_message)]},
            {"recursion_limit": RECURSION_LIMIT},
            stream_mode="values",
    ):
        log = step["messages"][-1].pretty_repr()
        formatted_log = format_log_message(log)
        yield {"thought": formatted_log, "is_final": False, "final_content": None}
        last_step = step

    if last_step:
        final_content = last_step["messages"][-1].content
        yield {"thought": "Final response processing.", "is_final": True,
               "final_content": final_content}
    else:
        yield {"thought": "Agent did not produce a response.", "is_final": True,
               "final_content": None}


# Left here to test the agent alone
if __name__ == '__main__':
    # for step in agent.stream(
    #     {"messages": [system_prompt, HumanMessage(content=user_message)]},
    #     {"recursion_limit": RECURSION_LIMIT},
    #     stream_mode="values",
    # ):
    #     step["messages"][-1].pretty_print()
    print(trigger_agent(user_message)['messages'][-1].content)
