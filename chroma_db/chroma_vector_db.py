import logging
from typing import List, Optional, TypedDict, Union

import chromadb
from chromadb.api.models.Collection import Collection
from utils.status import Status
import traceback
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

    def perform_similarity_search(
        self,
        k: int,
        user_profile_embedding: List[float],
        return_scores: bool = False,
        min_similarity: float = 0.0
    ) -> Optional[Union[List[str], tuple[List[str], List[float]]]]:
        """
        Perform similarity search on ChromaDB.

        Args:
            k (int): No. of top similar results to return (ignored when min_similarity > 0)
            user_profile_embedding (List[float]): Embedding vector of the user profile
            return_scores (bool): Whether to return similarity scores along with IDs
            min_similarity (float): Minimum similarity score (0-1) to include in results

        Returns:
            Union[List[str], tuple[List[str], List[float]]]:
            - If return_scores=False: List of top-k hashes (ids) of similar items
            - If return_scores=True: Tuple of (paper_ids, similarity_scores)
            - None if error occurs
        """
        try:
            # Get total number of documents in collection
            total_docs = self.collection.count()

            if total_docs == 0:
                logger.warning("ChromaDB collection is empty!")
                return []  # todo check if this works

            # If we're filtering by similarity, get ALL papers to check their similarity
            if min_similarity > 0:
                n_results = total_docs
            else:
                n_results = k

            # Include distances only if we need scores
            include_params = ["metadatas"]
            if return_scores or min_similarity > 0:
                include_params.append("distances")

            results = self.collection.query(
                query_embeddings=[user_profile_embedding],
                n_results=n_results,
                include=include_params  # type: ignore
            )

            ids_result = results.get("ids", [[]])
            ids = ids_result[0] if ids_result else []
            logger.info(f"Similarity search returned {len(ids)} results: {ids}")

            if not ids:
                return None

            # If we don't need scores, return just the IDs
            if not return_scores and min_similarity == 0.0:
                return ids

            # Get distances for score calculation
            distances_result = results.get("distances", [[]])
            distances = distances_result[0] if distances_result else []

            if not distances:
                return None

            # Convert distances to similarity scores and filter
            filtered_ids = []
            filtered_scores = []

            for paper_id, distance in zip(ids, distances):
                if paper_id is not None and distance is not None:
                    similarity_score = 1 - distance
                    if similarity_score >= min_similarity:
                        filtered_ids.append(paper_id)
                        filtered_scores.append(similarity_score)

            return filtered_ids, filtered_scores

        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return None

    def count_documents(self) -> int:
        return self.collection.count()

    def get_embedding_by_hash(self, paper_hash: str) -> Optional[List[float]]:
        """
        Get embedding for a specific paper hash from ChromaDB.

        Args:
            paper_hash (str): The paper hash to look up

        Returns:
            List[float]: The embedding vector for the paper, or None if not found
        """
        try:
            results = self.collection.get(
                ids=[paper_hash],
                include=["embeddings"]
            )

            embeddings = results.get("embeddings", [])
            logger.debug(
                f"Raw embeddings result for {paper_hash}: {type(embeddings)}, length: {len(embeddings) if embeddings is not None else 'None'}")

            if embeddings is not None and len(embeddings) > 0:
                embedding = embeddings[0]
                # Handle both numpy arrays and regular lists
                if embedding is not None:
                    # Convert to List[float] - handle both numpy arrays and regular lists
                    if isinstance(embedding, (list, tuple)):
                        return [float(x) for x in embedding]
                    else:
                        # Try to convert numpy array or other types
                        try:
                            return [float(x) for x in embedding]
                        except (TypeError, ValueError):
                            logger.warning(f"Unexpected embedding type for paper hash {paper_hash}: {type(embedding)}")
                            return None
                return None
            else:
                logger.warning(f"No embedding found for paper hash: {paper_hash}")
                return None

        except Exception as e:
            logger.error(f"Error getting embedding for paper hash {paper_hash}: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None


# Instantiate singleton
# todo find a better approach for this
chroma_db = ChromaVectorDB()
