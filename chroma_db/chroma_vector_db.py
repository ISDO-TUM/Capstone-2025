import logging
from typing import List, Optional, TypedDict

import chromadb
from chromadb.api.models.Collection import Collection
from utils.status import Status

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PaperData(TypedDict):
    embedding: List[float]
    hash: str


class ChromaVectorDB:
    def __init__(self, collection_name: str = "research-papers", outside_docker = False) -> None:
        # UNCOMMENT THIS FOR LOCAL TESTING ONLY;
        if outside_docker:
            self.client = chromadb.HttpClient(host="localhost", port=8000)
        # THIS SHOULD BE USED IN PRODUCTION
        else:
            self.client = chromadb.HttpClient(host="chromadb", port=8000)
        self.collection: Collection = self.client.get_or_create_collection(collection_name)

    def store_embeddings(self, data: List[PaperData]) -> int:
        """
        Store text embeddings in Chroma using OpenAI API.

        Args:
            data: list of dicts like {"hash": str, "embedding": List[float]}

        Returns:
            status_code: Status.SUCCESS if all succeeded, Status.FAILURE if any failed
        """
        any_failure = False

        for item in data:
            try:
                hash_id = item["hash"]
                embedding = item["embedding"]

                self.collection.upsert(
                    ids=[hash_id],
                    embeddings=[embedding],
                )

            except Exception as e:
                logger.error(f"Failed to store embedding for hash={item.get('hash')}: {e}")
                any_failure = True

        return Status.FAILURE if any_failure else Status.SUCCESS

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
                include=["metadatas"]
            )

            # The IDs are returned in the results even without specifying them in include
            return results.get("ids", [[]])[0]

        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return None

    def count_documents(self) -> int:
        return self.collection.count()


# Instantiate singleton
# todo find a better approach for this
chroma_db = ChromaVectorDB()
