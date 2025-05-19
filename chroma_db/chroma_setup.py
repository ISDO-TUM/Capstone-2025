import chromadb
from chromadb.config import Settings

chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="my_collection")

collection.add(
    documents=[
        "This is a document about pineapple",
        "This is a document about beer"
    ],
    ids=["id1", "id2"]
)

results = collection.query(
    query_texts=["This is a query document about munich"], # Chroma will embed this for you
    n_results=2 # how many results to return
)
print(results)

