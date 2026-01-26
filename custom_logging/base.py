from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from contextvars import ContextVar
import logging


# Context variables for storing request-scoped information
project_id_ctx: ContextVar[str] = ContextVar("project_id", default="")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="")


class LogContext(BaseModel):
    """
    Contextual information that is automatically included in every log entry.

    Attributes:
        project_id (str): Identifier for the current project.
        user_id (str): Identifier for the current user.
        component (str): Name of the logging component.
    """

    project_id: str = Field(..., description="Project identifier")
    user_id: str = Field(..., description="User identifier")
    component: str = Field(..., description="Logger component name")


class LogData(BaseModel):
    """
    Complete log entry data structure with context, level, and custom fields.

    Attributes:
        context (LogContext): Automatic contextual information.
        level (Literal): The severity level of the log entry.
        extra_fields (Optional[dict[str, Any]]): Additional structured metadata specific to this log entry.
    """

    context: LogContext
    level: Literal["INFO", "ERROR", "WARNING", "DEBUG", "CRITICAL"]
    extra_fields: Optional[dict[str, Any]] = None


class StructuredLogger:
    """
    A structured logger that automatically enriches log entries with context. This logger provides a structured logging interface that automatically includes project, user, and component context in every log entry.
    """

    def __init__(self, name: str):
        """
        Initialize a structured logger instance.

        Args:
            name (str): The name of the logger, typically representing the component.
        """
        self.logger = logging.getLogger(name)
        self.component = name
        self.project_id = "unknown"
        self.user_id = "unknown"

    def _log_with_context(self, message: str, metadata: LogData):
        """
        Internal method to handle the actual logging with structured data. This method flattens the LogData structure so that context fields and extra_fields are merged at the top level for easier queryin in log aggregation systems.

        Args:
            message (str): The primary log message.
            metadata (LogData): Structured log data with context and level.
        """
        extra = metadata.model_dump()

        context_dict = extra.pop("context", {})
        extra.update(context_dict)

        extra_fields_dict = extra.pop("extra_fields", {})
        extra.update(extra_fields_dict)

        log_method = getattr(self.logger, metadata.level.lower())
        log_method(message, extra=extra)

    def _get_current_context(self, state: Optional[Any] = None) -> LogContext:
        """
        Retrieve the current logging context. Prioritizes values from `state` if provided, then falls back to ContextVar.

        Returns:
            LogContext: The current context with project, user, and component name
        """
        self.project_id = getattr(state, "project_id", project_id_ctx.get()) if state else project_id_ctx.get()
        self.user_id = getattr(state, "user_id", user_id_ctx.get()) if state else user_id_ctx.get()

        return LogContext(
            project_id=self.project_id,
            user_id=self.user_id,
            component=self.component,
        )

    def info(
        self, message: str, metadata: Optional[dict] = None, state: Optional[Any] = None
    ):
        """
        Log an informational message.

        Args:
            message (str): Description of what happened.
            metadata (Optional[dict]): Additional structured data relevant to this specific event.
        """
        context = self._get_current_context(state=state)
        log_data = LogData(
            context=context,
            level="INFO",
            extra_fields=metadata,
        )
        self._log_with_context(message, log_data)

    def warning(self, message: str, metadata: Optional[dict] = None):
        """
        Log a warning message.

        Args:
            message (str): Description of warning condition.
            metadata (Optional[dict]): Context about the warning.
        """
        context = self._get_current_context()
        log_data = LogData(context=context, level="WARNING", extra_fields=metadata)
        self._log_with_context(message, log_data)

    def debug(self, message: str, metadata: Optional[dict] = None):
        """
        Log a debug message.

        Args:
            message (str): Detailed diagnostic information.
            metadata (Optional[dict]): Technical details useful for debugging.
        """
        context = self._get_current_context()
        log_data = LogData(
            context=context,
            level="DEBUG",
            extra_fields=metadata,
        )
        self._log_with_context(message, log_data)

    def error(self, message: str, metadata: Optional[dict] = None):
        """
        Log an error message.

        Args:
            message (str): Description of the error.
            metadata (Optional[dict]): Error context such as input parameters or stack traces.
        """
        context = self._get_current_context()
        log_data = LogData(
            context=context,
            level="ERROR",
            extra_fields=metadata,
        )
        self._log_with_context(message, log_data)

    def critical(self, message: str, metadata: Optional[dict] = None):
        """
        Log a critical message.

        Args:
            message (str): Description of the critical failure.
            metadata (Optional[dict]): Critical context.
        """
        context = self._get_current_context()
        log_data = LogData(
            context=context,
            level="CRITICAL",
            extra_fields=metadata,
        )
        self._log_with_context(message, log_data)
