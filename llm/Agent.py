"""
Legacy agent orchestration for the Capstone project (React agent).

Responsibilities:
- Provides functions to trigger the agent and stream its thought process
- Uses a system prompt and tools to invoke the agent
- Used for testing and legacy flows (superseded by StategraphAgent)
"""

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
    """
    Invoke the agent with a user message and return the final response.
    Args:
        user_message (str): The user's input message.
    Returns:
        dict: The agent's response object.
    """
    return agent.invoke({'messages': [system_prompt, HumanMessage(content=user_message)]})


def trigger_agent_show_thoughts(user_message: str):
    """
    Generator that yields each step of the agent's thought process for frontend streaming.
    Args:
        user_message (str): The user's input message.
    Yields:
        dict: Thought and state at each step, including final output.
    """
    last_step = None

    for step in agent.stream(
            {"messages": [system_prompt, HumanMessage(content=user_message)]},
            stream_mode="values",
    ):
        log = step["messages"][-1].pretty_repr()
        # print(log)
        formatted_log = format_log_message(log)
        print(log)
        yield {"thought": formatted_log, "is_final": False, "final_content": None}
        last_step = step

    if last_step:
        final_content = last_step["messages"][-1].content
        yield {"thought": "Final response processing.", "is_final": True,
               "final_content": final_content}
    else:
        yield {"thought": "Agent did not produce a response.", "is_final": True,
               "final_content": None}


# NOTE: This block is for local testing only. Uncomment to run local tests.
# if __name__ == '__main__':
#     # for step in agent.stream(
#     #     {"messages": [system_prompt, HumanMessage(content=user_message)]},
#     #     {"recursion_limit": RECURSION_LIMIT},
#     #     stream_mode="values",
#     # ):
#     #     step["messages"][-1].pretty_print()
#     print(trigger_agent(user_message)['messages'][-1].content)
