from custom_logging.base import StructuredLogger


class APILogger(StructuredLogger):
    def __init__(self):
        super().__init__("api")

    def request_start(self, method: str, path: str):
        self.info(
            f"API request started for path: {path}",
            metadata={
                "method": method,
                "path": path,
            },
        )

    def request_error(
        self, method: str, path: str, error_message: str, status_code: int
    ):
        self.error(
            f"API request error for path: {path}",
            metadata={
                "method": method,
                "path": path,
                "error_message": error_message,
                "status_code": status_code,
            },
        )

    def request_success(self, method: str, path: str, status_code: int):
        self.info(
            f"API request successful for path: {path}",
            metadata={
                "method": method,
                "path": path,
                "status_code": status_code,
            },
        )

    def request_warning(self, method: str, path: str, warning_message: str):
        self.warning(
            "API request warning",
            metadata={
                "method": method,
                "path": path,
                "warning_message": warning_message,
            },
        )

    def request_info(self, method: str, path: str, info_message: str):
        self.info(
            f"API request info: {info_message}",
            metadata={"method": method, "path": path, "info_message": info_message},
        )
