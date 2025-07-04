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


# When locally testing application and files this will allow us to set a localhost connection
# since otherwise the application will try to connect to the Docker container, which the file
# is running outside of and hence does not have access to.
# In production, the Docker container will set these env-vars to the correct values.
# For testing run like this:
# docker compose up -d chromadb
# CHROMA_HOST=localhost python -m llm.tools.paper_handling_tools
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")   # default for Docker
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))


class ChromaVectorDB:

    def __init__(self, collection_name: str = "research-papers") -> None:
        # single code-path, host decided by env-var
        self.client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
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
