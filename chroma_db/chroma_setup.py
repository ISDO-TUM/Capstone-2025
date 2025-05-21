import chromadb

from chromadb import Client
from chromadb.config import Settings

client = chromadb.PersistentClient(path="./chroma_storage")
collection = client.get_or_create_collection(name="research-papers")

collection.add(
    documents=[
        "This is a document about pineapple",
        "This is a document about beer"
    ],
    ids=["id1", "id2"]
)

results = collection.query(
    query_texts=["This is a query document about munich"], # Chroma will embed this
    n_results=2 # how many results to return
)
print(results)

