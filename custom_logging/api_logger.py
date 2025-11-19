from custom_logging.base import StructuredLogger


class APILogger(StructuredLogger):
    def __init__(self):
        super().__init__("api")

    def request_start(self, method: str, path: str):
        self.info(
            "API request started",
            metadata={
                "method": method,
                "path": path,
            },
        )

    # ========== TODO ==========
