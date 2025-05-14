from llm.Prompting import llm_call
from llm.Prompts import TriggerS, RatingH, RatingS
from paper_handling.paper_metadata_retriever import get_multiple_topic_works, \
    get_mulitple_topic_works_titles

user_description = """
I'm researching the application of transformer-based language models in biomedical text mining.
Specifically, I'm interested in methods for extracting relationships between genes, diseases,
and drugs from scientific publications, as well as improvements in named entity recognition and
domain-specific fine-tuning strategies in the biomedical domain.
"""


def agent_start():
    keywords = llm_call(TriggerS, user_description)
    if keywords == -1:
        return -1
    string_array = [s.strip() for s in keywords.split(",")]

    retrieved_papers = get_mulitple_topic_works_titles(get_multiple_topic_works(string_array))

    human_message = RatingH.format(
        user_description=user_description,
        retrieved_papers=retrieved_papers
    )
    result = llm_call(RatingS, human_message)
    print(result)
    return 0


if __name__ == '__main__':
    agent_start()
