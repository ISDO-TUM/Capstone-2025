"""
ChromaDB vector search wrapper for the Capstone project.

Responsibilities:
- Provides a class for storing and retrieving paper embeddings in ChromaDB
- Supports similarity search, filtering, and embedding retrieval by hash
- Used for all vector search and ranking operations in the agent and ingestion flows
- Handles both local and Docker-based ChromaDB connections
"""

import logging
from typing import List, Optional, TypedDict, Union

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings
from utils.status import Status
import traceback
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

# Ensure telemetry is disabled for all Chroma clients (HTTP or in-memory).
try:
    chromadb.configure(anonymized_telemetry=False)
except Exception as exc:  # best-effort; fall back silently if configure fails
    logger.warning("Failed to configure Chroma telemetry settings: %s", exc)

# Some versions of Chroma still instantiate the Posthog client even when
# anonymized telemetry is disabled. Force-disable capture so no network
# calls are attempted and the noisy log errors stop.
try:
    import posthog

    posthog.disabled = True

    def _noop_capture(*_args, **_kwargs):
        return None

    posthog.capture = _noop_capture  # type: ignore[assignment]
except Exception as exc:
    logger.warning("Failed to override Posthog telemetry capture: %s", exc)


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
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")  # default for Docker
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))


USE_IN_MEMORY_DB = os.getenv("USE_IN_MEMORY_DB", "").lower() == "true"
def _build_in_memory_client(settings: Settings):
    """Create an in-memory Chroma client honoring telemetry settings."""
    ephemeral_cls = getattr(chromadb, "EphemeralClient", None)
    if callable(ephemeral_cls):
        return ephemeral_cls(settings=settings)

    # Fallback for older Chroma releases without EphemeralClient
    return chromadb.Client(
        Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=None,
            anonymized_telemetry=settings.anonymized_telemetry,
        )
    )


class ChromaVectorDB:
    """
    Wrapper class for ChromaDB operations: storing, searching, and retrieving embeddings.
    """

    def __init__(
        self,
        collection_name: str = "research-papers",
        use_in_memory: Optional[bool] = None,
    ) -> None:
        """
        Initialize the ChromaVectorDB client and collection.
        Args:
            collection_name (str): The name of the ChromaDB collection to use.
            use_in_memory (Optional[bool]): Force in-memory Chroma client if True. When
                None, defaults to USE_IN_MEMORY_DB environment variable.
        """
        self.use_in_memory = USE_IN_MEMORY_DB if use_in_memory is None else use_in_memory
        settings = Settings(anonymized_telemetry=False)

        if self.use_in_memory:
            logger.info("ChromaVectorDB running in in-memory mode")
            self.client = _build_in_memory_client(settings)
        else:
            logger.info(
                "Connecting to ChromaDB host=%s port=%s (telemetry disabled)",
                CHROMA_HOST,
                CHROMA_PORT,
            )
            self.client = chromadb.HttpClient(
                host=CHROMA_HOST,
                port=CHROMA_PORT,
                settings=settings,
            )

        self.collection: Collection = self.client.get_or_create_collection(
            collection_name
        )

    def store_embeddings(self, data: List[PaperData]) -> int:
        """
        Store text embeddings in Chroma using OpenAI API.
        Args:
            data (List[PaperData]): List of dicts like {"hash": str, "embedding": List[float]}
        Returns:
            int: Status.SUCCESS if all succeeded, Status.FAILURE if any failed
        Side effects:
            Upserts embeddings into the ChromaDB collection.
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
                logger.error(
                    f"Failed to store embedding for hash={item.get('hash')}: {e}"
                )
                any_failure = True

        return Status.FAILURE if any_failure else Status.SUCCESS

    def perform_similarity_search(
        self,
        k: int,
        user_profile_embedding: List[float],
        return_scores: bool = False,
        min_similarity: float = 0.0,
    ) -> Optional[Union[List[str], tuple[List[str], List[float]]]]:
        """
        Perform similarity search on ChromaDB.
        Args:
            k (int): Number of top similar results to return (ignored when min_similarity > 0)
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
                return []

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
                include=include_params,  # type: ignore
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
        """
        Count the number of documents in the ChromaDB collection.
        Returns:
            int: Number of documents in the collection.
        """
        return self.collection.count()

    def get_embedding_by_hash(self, paper_hash: str) -> Optional[List[float]]:
        """
        Get embedding for a specific paper hash from ChromaDB.
        Args:
            paper_hash (str): The paper hash to look up
        Returns:
            Optional[List[float]]: The embedding vector for the paper, or None if not found
        """
        try:
            results = self.collection.get(ids=[paper_hash], include=["embeddings"])

            embeddings = results.get("embeddings", [])
            logger.debug(
                f"Raw embeddings result for {paper_hash}: {type(embeddings)}, length: {len(embeddings) if embeddings is not None else 'None'}"
            )

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
                            logger.warning(
                                f"Unexpected embedding type for paper hash {paper_hash}: {type(embedding)}"
                            )
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
