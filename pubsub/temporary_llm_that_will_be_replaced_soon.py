from langchain_core.prompts import ChatPromptTemplate

from llm.LLMDefinition import LLM

llm = LLM

prompt = ChatPromptTemplate.from_template(
    """You are a research assistant. Given the following list of paper matadata including abstracts, select the top {k} that are most relevant to the following user project description: "{topic}"
    Also write for each selected papers a short, non verbose summary based on the paper's abstract or title if the abstract is not available, and the project description on why the paper is relevant to the user.
    Papers:
{papers}

Respond with a dict list of the paper hashes of the most relevant papers. With the following form:
    Example:
        [
            {{
            "paper_hash": <paper hash>
            "summary": <short summary>
            }},
            {{
            "paper_hash": <paper hash>
            "summary": <short summary>
            }},
        ...
        ]
"""
)


def calL_temp_agent(papers: str, project_prompt: str, k: str):
    formatted_prompt = prompt.format_messages(
        topic=project_prompt,
        papers=papers,
        k=k
    )
    return llm.invoke(formatted_prompt)
