from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input = [text], model=model).data[0].embedding
