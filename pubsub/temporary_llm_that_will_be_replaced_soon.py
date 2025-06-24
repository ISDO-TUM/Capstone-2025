from langchain_core.prompts import ChatPromptTemplate

from llm.LLMDefinition import LLM

llm = LLM

prompt = ChatPromptTemplate.from_template(
    """You are a research assistant. Given the following list of paper matadata including abstracts, select the top {k} that are most relevant to the following user project description: "{topic}"

Papers:
{papers}

Respond with a JSON list of the paper hashes of the most relevant papers.
"""
)


def calL_temp_agent(papers: str, project_prompt: str, k: str):
    formatted_prompt = prompt.format_messages(
        topic=project_prompt,
        papers=papers,
        k=k
    )
    return llm.invoke(formatted_prompt)
