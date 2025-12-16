import logging


class ColorFormatter(logging.Formatter):
    """
    A custom logging formatter that adds ANSI color codes to log levels. This formatter enhances terminal log output by colorizing log levels according to their severity, making it easier to quickly identify different types of log messages at a glance.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"  # ANSI reset code to restore default terminal formatting

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with colorized level names.

        Args:
            record (logging.LogRecord): The log record to be formatted.

        Returns:
            str: The formatted log message with colorized level name.
        """
        original_level = record.levelname
        color = self.COLORS.get(original_level, "")
        colored_level = f"{color}{original_level:8}{self.RESET}"

        format_str = "%(asctime)s %(levelname)-8s %(message)s"
        formatter = logging.Formatter(format_str, datefmt="%H:%M:%S")

        record.levelname = colored_level
        result = formatter.format(record)
        record.levelname = original_level

        return result
