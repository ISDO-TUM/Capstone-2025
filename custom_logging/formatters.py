import logging


class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m'    # Red background
    }
    RESET = '\033[0m'

    def format(self, record):
        original_level = record.levelname
        color = self.COLORS.get(original_level, '')
        colored_level = f"{color}{original_level:8}{self.RESET}"

        format_str = '%(asctime)s %(levelname)-8s %(message)s'
        formatter = logging.Formatter(format_str, datefmt='%H:%M:%S')

        record.levelname = colored_level
        result = formatter.format(record)
        record.levelname = original_level

        return result
