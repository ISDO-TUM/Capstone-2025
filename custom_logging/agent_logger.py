from custom_logging.base import StructuredLogger
from contextvars import ContextVar
from typing import Optional, Any
from database.projects_database_handler import get_log_history_flag

user_query_ctx: ContextVar[str] = ContextVar("user_query", default="")


class AgentLogger(StructuredLogger):
    """
    A specialized structured logger for agent-based workflows. The logger maintains a pending metadata store that accumulates context across multiple operations within a node, which is automatically included in completion logs.
    """

    def __init__(self):
        """
        Initialize the AgentLogger. Sets up the logger with the name "agent" and initializes an empty metadata dictionary for accumulating context across node operations.
        """
        super().__init__("agent")
        self._pending_metadata = {}
        self.node_name = "unknown node"

    def _user_consent_flag(self) -> bool:
        return get_log_history_flag(self.user_id, self.project_id)

    def set_user_query(self, user_query: str):
        """
        Set the current user query in context for all subsequent node logs.

        Args:
            user_query (str): The user query that initiated the agent workflow
        """
        user_query_ctx.set(user_query)

    def get_user_query(self) -> str:
        """
        Get the current user query from context.

        Returns:
            str: The current user query or empty string if not set
        """
        return user_query_ctx.get()

    def node_start(self, node_name: str, state: Optional[Any] = None, **metadata):
        """
        Log the start of a node execution. This should be called when a node begins processing.

        Args:
            node_name (str): The name of the node being executed.
            **metadata: Additional key-value pairs to include in the log metadata.
        """
        if not self._user_consent_flag():
            metadata = dict()

        self.node_name = node_name
        self.info(
            f"Node {node_name} started - project_id={self.project_id}",
            metadata={"node_name": node_name, **metadata},
            state=state,
        )

    def node_complete(
        self, node_name: str, state: Optional[Any] = None, metadata: dict = None
    ):
        """
        Log the successful completion of a node execution. This should be called when a node finishes processing successfully. Automatically includes any accumulated metadata from `add_metadata()` and clears the pending metaadata store.

        Args:
            node_name (str): The name of the completed node.
            metadata (dict): Node-specific completion data.
        """
        if not self._user_consent_flag():
            metadata = dict()

        self.info(
            f"Node {node_name} completed - project_id={self.project_id}",
            metadata={"node_name": node_name, **self._pending_metadata, **metadata},
            state=state,
        )
        self.node_name = "unknown node"
        self.clear_metadata()

    def node_error(self, error: Exception | str, **metadata):
        """
        Log an error that occurred during node execution. This should be called when a node encounters an error. Automatically includes any accumulated metadata from `add_metadata()` and clears the pending metadata store.

        Args:
            node_name (str): The name of the node where the error occurred.
            error (Exception | str): The error that occurred, either as an Exception object or string.
            **metadata: Additional key-value pairs to include in the error log metadata.
        """
        if not self._user_consent_flag():
            metadata = dict()

        error_message = str(error) if isinstance(error, Exception) else error
        self.error(
            f"Node {self.node_name} error - project_id={self.project_id}",
            metadata={
                "node_name": self.node_name,
                "error": error_message,
                "error_type": error.__class__.__name__
                if isinstance(error, Exception)
                else "str",
                **self._pending_metadata,
                **metadata,
            },
        )
        self.clear_metadata()

    def add_metadata(self, metadata: dict):
        """
        Add metadata to be included in subsequent node completion.

        Args:
            metadata (dict): Key-value pairs to add to the pending metadata store.
        """
        self._pending_metadata.update(metadata)

    def clear_metadata(self):
        """
        Clear the pending metadata store when you don't want the accumulated data to be included in future logs.
        """
        self._pending_metadata.clear()
