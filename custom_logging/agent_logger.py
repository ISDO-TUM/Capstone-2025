from custom_logging.base import StructuredLogger


class AgentLogger(StructuredLogger):
    def __init__(self):
        super().__init__("agent")
        self._pending_metadata = {}

    def node_start(self, node_name: str, user_query: str):
        self.info(
            "Node started",
            metadata={
                "node_name": node_name,
                "user_query": user_query,
            },
        )

    def node_complete(self, node_name: str, metadata: dict):
        self.info(
            "Node completed",
            metadata={"node_name": node_name, **self._pending_metadata, **metadata},
        )
        self.clear_metadata()

    def add_metadata(self, metadata):
        self._pending_metadata.update(metadata)

    def clear_metadata(self):
        self._pending_metadata.clear()
