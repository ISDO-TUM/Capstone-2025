from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from contextvars import ContextVar
import logging


project_id: ContextVar[str] = ContextVar('project_id', default='')
user_id: ContextVar[str] = ContextVar('user_id', default='')


class LogContext(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    user_id: str = Field(..., description="User identifier")
    component: str = Field(..., description="Logger component name")


class LogData(BaseModel):
    context: LogContext
    level: Literal["INFO", "ERROR", "WARNING", "DEBUG", "CRITICAL"]
    extra_fields: Optional[dict[str, Any]] = None


class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.component = name

    def _log_with_context(self, message: str, metadata: LogData):
        extra = metadata.model_dump()

        context_dict = extra.pop("context", {})
        extra.update(context_dict)

        extra_fields_dict = extra.pop("extra_fields", {})
        extra.update(extra_fields_dict)

        log_method = getattr(self.logger, metadata.level.lower())
        log_method(message, extra=extra)

    def _get_current_context(self) -> LogContext:
        return LogContext(
            project_id=project_id.get() or "unknown",
            user_id=user_id.get() or "unknown",
            component=self.component
        )

    def info(self, message: str, metadata: Optional[dict] = None):
        context = self._get_current_context()
        log_data = LogData(
            context=context,
            level="INFO",
            extra_fields=metadata,
        )
        self._log_with_context(message, log_data)
