from llm.Embeddings import embed_string
from chromadb.api.models.Collection import Collection
import chromadb
from typing import List, Dict, Optional
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ChromaVectorDB:
    def __init__(self, collection_name: str = "research-papers") -> None:
        self.client = chromadb.HttpClient(host="localhost", port=8000)
        self.collection: Collection = self.client.get_or_create_collection(collection_name)

    def store_embeddings(self, data: List[Dict[str, str]]) -> int:
        """
        Store text embeddings in Chroma using OpenAI API.

        Args:
            data: list of dicts like {"hash": str, "text": str}

        Returns:
            status_code: 0 if all succeeded, 1 if any failed
        """
        errors = 0

        for item in data:
            try:
                hash_id = item["hash"]
                text = item["text"]

                embedding = embed_string(text)

                self.collection.upsert(
                    ids=[hash_id],
                    embeddings=[embedding],
                    documents=[text]
                )

            except Exception as e:
                logger.error(f"Failed to store embedding for hash={item.get('hash')}: {e}")
                errors += 1

        return 1 if errors else 0

    def perform_similarity_search(self, k: int, user_profile_embedding: List[float]) -> Optional[List[str]]:
        """
        Perform similarity search on ChromaDB.

        Args:
            k (int): No. of top similar results to return
            user_profile_embedding (List[float]): Embedding vector of the user profile

        Returns:
            List[str]: List of top-k hashes (ids) of similar items
            or None if error occurs
        """
        try:
            results = self.collection.query(
                query_embeddings=[user_profile_embedding],
                n_results=k,
                include=["ids"]
            )

            return results.get("ids", [[]])[0]

        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return None

    def count_documents(self) -> int:
        return self.collection.count()
