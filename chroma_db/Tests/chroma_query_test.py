import chromadb

client = chromadb.HttpClient(host="chromadb", port=8000)

collection = client.get_or_create_collection("research-papers")

print(f"Total documents in collection: {collection.count()}")

results = collection.query(
    query_texts=[
        "provide papers about climate change impacts in Brazil"
    ],  # add your query
    n_results=5,
)

print("Most relevant papers:\n")
for doc in results["documents"][0]:
    print("-", doc)
