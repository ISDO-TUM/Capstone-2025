from chroma_db.chroma_vector_db import ChromaVectorDB

sample_data = [
    {"hash": "abc123", "text": "This is a test abstract about AI."},
    {"hash": "def456", "text": "Another text about climate and research."}
]

db = ChromaVectorDB()
status = db.store_embeddings(sample_data)

print(f"Status code: {status}")
print(f"Total documents in Chroma: {db.count_documents()}")
