from custom_logging.base import StructuredLogger


class AgentLogger(StructuredLogger):
    def __init__(self):
        super().__init__("agent")

    # ========== TODO ==========
