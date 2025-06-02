import chromadb
from paper_handling.paper_handler import fetch_works_multiple_queries
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Setup Chroma client and collection
client = chromadb.HttpClient(host="chromadb", port=8000)

# Delete collection if it already exists, to start fresh
try:
    client.delete_collection("research-papers")
except Exception as e:
    print(f"Collection deletion failed: {e}")

# Now create collection again
collection = client.get_or_create_collection("research-papers")
# Define topic keywords
queries = [
    "biomedical",
    "large language models",
    "climate change",
    "biodiversity",
    "sustainability",
    "quantum computing",
    "social networks",
]  # add preferred keywords


# Fetch papers from OpenAlex
papers = fetch_works_multiple_queries(queries)
print("Papers fetched:", len(papers))  # Debug line


# Add papers to Chroma
for paper in papers:
    paper_id = paper["id"]
    title = paper.get("title", "No title")
    abstract = paper.get("abstract", "")
    authors = paper.get("authors", "Unknown")
    pdf_url = paper.get("pdf_url") or paper.get("landing_page_url", "")

    content = f"{title}\n\n{abstract}"

    collection.upsert(
        ids=[paper_id],
        documents=[content],
        metadatas=[{"title": title, "authors": authors, "url": pdf_url}],
    )

print(f"Added: {title[:200]}...")

print(f"Ingested {collection.count()} papers into Chroma collection 'research-papers'")
