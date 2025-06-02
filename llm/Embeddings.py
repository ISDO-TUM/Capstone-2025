from openai import OpenAI

from llm.LLMDefinition import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def embed_string(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding


def embed_user_profile(text):
    return embed_string(text)


def embed_papers(title, abstract, hash):
    return embed_string(title + abstract), hash
